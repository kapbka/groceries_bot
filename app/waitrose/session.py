import requests
from python_graphql_client import GraphqlClient
from app.waitrose import constants
import logging
from datetime import datetime
from app.log import app_exception
import http


class Session:
    def __init__(self, login: str, password: str):
        self.login = login
        self.password = password
        self.client = GraphqlClient(endpoint=constants.SESSION_ENDPOINT_URL)

        self.token = None
        try:
            session_data = self.execute(
                constants.SESSION_QUERY,
                {"session": {"username": login, "password": password, "customerId": "-1", "clientId": "WEB_APP"}})
        except requests.exceptions.HTTPError as err:
            if err.response.status_code == 401:
                raise app_exception.LoginFailException
            elif err.response.status_code == 500:
                raise app_exception.ShopProviderUnavailableException
            else:
                raise app_exception.ConnectionException
        except requests.ConnectionError:
            raise app_exception.ConnectionException
        except requests.exceptions.RequestException as e:
            raise

        self.token = session_data['data']['generateSession']['accessToken']
        if self.token is None:
            raise app_exception.LoginFailException(user_err_msg=session_data['data']['generateSession']['failures'][0]['message'])

        self.headers = {'authorization': f"Bearer {self.token}"}
        self.customerId = int(session_data['data']['generateSession']['customerId'])
        self.customerOrderId = int(session_data['data']['generateSession']['customerOrderId'])

        address_list = self.get_address_list()
        self.default_address_id = address_list[0]['id']
        self.default_postcode = address_list[0]['postalCode']
        self.phone_number = address_list[0]['addressee']['contactNumber']
        postcode_branches = requests.get(constants.BRANCH_ID_BY_POSCODE_URL.format(self.default_postcode),
                                         headers=self.headers).json()
        if postcode_branches or postcode_branches['totalCount'] >= 1:
            self.default_branch_id = [branch['branch']['id'] for branch in postcode_branches['branches']
                                      if branch['defaultBranch']][0]

    def execute(self, query: str, variables: dict):
        logging.debug(variables)
        return self.client.execute(
                query=query,
                variables=variables,
                headers=self.headers if self.token else {})

    def get_address_list(self):
        r = requests.get(constants.LAST_ADDRESS_ID_URL, headers=self.headers).json()
        if not r:
            raise app_exception.NoAddressException
        return r

    def get_order_dict(self):
        r = requests.get(constants.ORDER_LIST_URL, headers=self.headers).json()
        return {order['customerOrderId']: order for order in r['content']}

    def _get_orders(self):
        r = requests.get(constants.ORDER_LIST_URL, headers=self.headers)
        if r.status_code != http.HTTPStatus.OK:
            raise app_exception.OrderListException
        res = r.json()
        if not res['content']:
            raise app_exception.NoOrdersException
        return res

    def get_last_order_date(self):
        orders = self._get_orders()
        return datetime.strptime(orders['content'][0]['slots'][0]['startDateTime'], '%Y-%m-%dT%H:%M:%S.%fZ').date()

    def order_exists(self, slot_datetime):
        orders = self._get_orders()
        for order in orders['content']:
            order_datetime = datetime.strptime(order['slots'][0]['startDateTime'], '%Y-%m-%dT%H:%M:%S.%fZ').date()
            if order_datetime == slot_datetime:
                logging.info(f'Order already exists {order_datetime}')
                return True
        return False

    def merge_last_order_to_trolley(self):
        try:
            order = next(iter(self.get_order_dict().values()))
        except StopIteration:
            logging.info('Orders not found1')
            raise app_exception.NoOrdersSlotBookedException

        logging.info('Getting products')
        line_num_qty_dict = {ol['lineNumber']: ol['quantity'] for ol in order['orderLines']}
        order_lines = '+'.join(ol for ol in line_num_qty_dict.keys())
        products = requests.get(constants.PRODUCT_LIST_URL.format(order_lines),
                                headers=self.headers).json() if order_lines else {}

        res = []
        for p in products['products']:
            if not p['markedForDelete']:
                pl = dict(canSubstitute='false',
                          lineNumber=str(p['lineNumber']),
                          productId=str(p['id']),
                          quantity=line_num_qty_dict[p['lineNumber']],
                          reservedQuantity=0,
                          trolleyItemId=-1)
                res.append(pl)

        logging.info('Getting items')
        items = requests.patch(constants.TROLLEY_ITEMS_URL.format(self.customerOrderId),
                               headers=self.headers, json=res).json() if res else {}

        # if there is no match the dict will contain 'message' key with the details what's wrong
        if 'message' in items:
            logging.exception(items['message'])
            raise ValueError(items['message'])

    def is_trolley_empty(self):
        variables = {"orderId": str(self.customerOrderId)}
        trolley = self.execute(constants.TROLLEY_QUERY, variables)
        failures = trolley['data']['getTrolley'].get('failures') or {}
        if failures.get('message'):
            raise app_exception.TrolleyException
        return not trolley['data']['getTrolley']['products']

    def get_payment_card_list(self):
        card_list = requests.get(constants.PAYMENTS_CARDS_URL, headers=self.headers).json()
        if not card_list:
            raise app_exception.NoPaymentCardException
        return card_list

    def get_card_id(self, card_num: int):
        cards = self.get_payment_card_list()
        for card in cards:
            if card['maskedCardNumber'].endswith(str(card_num)):
                return card['id']
        raise ValueError(f'Card number with last 4 digits "***{card_num}" is not found!')

    def checkout_trolley(self, card_id: int, cvv: int):
        # 1. CHECKOUT ORDER
        logging.info(f'Checkout: card_id {card_id}')
        checkout_param = {"addressId": str(self.default_address_id),
                          "cardSecurityCode": str(cvv)}
        checkout_resp = requests.put(constants.CHECKOUT_URL.format(str(self.customerOrderId), str(card_id)),
                                     headers=self.headers, json=checkout_param)
        logging.info(f'Checkout order response status code {checkout_resp.status_code}')
        if checkout_resp.status_code != http.HTTPStatus.CREATED:
            raise app_exception.PaymentException

        # 2. PLACE ORDER CONFIRMATION
        logging.info(f'Place order {self.customerOrderId}')
        place_param = {"contactNumber": self.phone_number,
                       "event": "PLACE",
                       "paperStatement": "false"}
        place_resp = requests.patch(constants.PLACE_ORDER_URL.format(str(self.customerOrderId)),
                                    headers=self.headers, json=place_param)
        logging.info(f'Place order response status code {place_resp.status_code}')
        if place_resp.status_code != http.HTTPStatus.OK:
            raise app_exception.PlaceOrderException

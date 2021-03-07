import requests
from python_graphql_client import GraphqlClient
from app.waitrose import constants
import logging
from datetime import datetime
from app.log import app_exception


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

    def get_last_order_date(self):
        r = requests.get(constants.ORDER_LIST_URL, headers=self.headers).json()
        if not r['content']:
            raise app_exception.NoOrdersException
        return datetime.strptime(r['content'][0]['lastUpdated'], '%Y-%m-%dT%H:%M:%S.%fZ').date()

    def merge_last_order_to_trolley(self):
        try:
            order = next(iter(self.get_order_dict().values()))
        except StopIteration:
            raise app_exception.NoOrdersSlotBookedException

        line_num_qty_dict = {ol['lineNumber']: ol['quantity'] for ol in order['orderLines']}
        order_lines = '+'.join(ol for ol in line_num_qty_dict.keys())
        products = requests.get(constants.PRODUCT_LIST_URL.format(order_lines),
                                headers=self.headers).json() if order_lines else {}

        res = []
        for p in products['products']:
            pl = dict(canSubstitute='false',
                      lineNumber=str(p['lineNumber']),
                      productId=str(p['id']),
                      quantity=line_num_qty_dict[p['lineNumber']],
                      reservedQuantity=0,
                      trolleyItemId=-1)
            res.append(pl)

        items = requests.patch(constants.TROLLEY_ITEMS_URL.format(self.customerOrderId),
                               headers=self.headers, json=res).json() if res else {}

        # if there is no match the dict will contain 'message' key with the details what's wrong
        if 'message' in items:
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
        param = {"addressId": str(self.default_address_id),
                 "cardSecurityCode": str(cvv)}

        res = requests.put(constants.CHECKOUT_URL.format(self.customerOrderId, card_id),
                           headers=self.headers, json=param).json()
        # TODO: check returned code and raise an exception if necessary
        return res['code']

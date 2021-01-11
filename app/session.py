import requests
from python_graphql_client import GraphqlClient
from app import constants


class Session:
    def __init__(self, login: str, password: str):
        self.login = login
        self.password = password
        self.client = GraphqlClient(endpoint=constants.SESSION_ENDPOINT_URL)

        self.token = None
        session_data = self.execute(
            constants.SESSION_QUERY,
            {"session": {"username": login, "password": password, "customerId": "-1", "clientId": "WEB_APP"}})
        self.token = session_data['data']['generateSession']['accessToken']
        self.headers = {'authorization': f"Bearer {self.token}"}
        self.customerId = int(session_data['data']['generateSession']['customerId'])
        self.customerOrderId = int(session_data['data']['generateSession']['customerOrderId'])

        account_data = requests.get(constants.ACCOUNT_URL, headers=self.headers).json()
        self.default_address_id = int(account_data['preferences']['defaultDeliveryAddressId'])
        self.default_branch_id = int(account_data['preferences']['defaultBranchId'])

        address_list = self.get_address_list()
        self.default_postcode = filter(lambda x: x['postalCode'] if x['id'] == self.default_address_id else None,
                                       address_list)

        orders = self.get_order_dict()
        self.last_order = next(iter(orders.values())) if orders else None
        self.last_order_id = int(self.last_order['customerOrderId'])

    def execute(self, query: str, variables: dict):
        return self.client.execute(
                query=query,
                variables=variables,
                headers=self.headers if self.token else {})

    def get_address_list(self):
        return requests.get(constants.LAST_ADDRESS_ID_URL, headers=self.headers).json()

    def get_order_dict(self):
        r = requests.get(constants.ORDER_LIST_URL, headers=self.headers).json()
        return {order['customerOrderId']: order for order in r['content']}

    def merge_order_to_trolley(self, order_id: int):
        order = self.get_order_dict()[str(order_id)]
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
                               headers=self.headers, json=res).json() if res else None

        # if there is no match the dict will contain 'message' key with the details what's wrong
        if items and 'message' in items:
            raise ValueError(items['message'])

    def is_trolley_empty(self):
        r = requests.get(constants.PRODUCT_LIST_URL.format(self.customerOrderId), headers=self.headers).json()
        return not r['trolley']['trolleyItems']

    def get_payment_card_list(self):
        return requests.get(constants.PAYMENTS_CARDS_URL, headers=self.headers).json()

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
        return res['code']

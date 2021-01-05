import requests
from python_graphql_client import GraphqlClient
from datetime import datetime, timedelta
from app import constants
import logging
import typing


class Session:
    def __init__(self, login: str, password: str):
        self.login = login
        self.password = password
        self.client = GraphqlClient(endpoint=constants.SESSION_ENDPOINT_URL)

        self.token = None
        data = self.execute(
            constants.SESSION_QUERY,
            {"session": {"username": login, "password": password, "customerId": "-1", "clientId": "WEB_APP"}})
        self.token = data['data']['generateSession']['accessToken']
        self.customerId = int(data['data']['generateSession']['customerId'])
        self.customerOrderId = int(data['data']['generateSession']['customerOrderId'])

        self.last_address_id = self._get_last_address_id()
        self.last_order = self._get_last_order()
        self.last_order_id = self._get_last_order_id()

    def get(self, url: str):
        res = None
        try:
            res = requests.get(url, headers={'authorization': f"Bearer {self.token}"}).json()
            return res
        except:
            logging.exception(f'Get request failed {res}')
            raise

    def put(self, url: str, json=None):
        res = None
        try:
            res = requests.put(url, headers={'authorization': f"Bearer {self.token}"}, json=json).json()
            return res
        except:
            logging.exception(f'Put request failed {res}')
            raise

    def patch(self, url: str, json=None):
        res = None
        try:
            res = requests.patch(url, headers={'authorization': f"Bearer {self.token}"}, json=json).json()
            return res
        except:
            logging.exception(f'Patch request failed {res}')
            raise

    def execute(self, query: str, variables: dict):
        res = None
        try:
            res = self.client.execute(
                query=query,
                variables=variables,
                headers={'authorization': f"Bearer {self.token}"} if self.token else {}
            )
            return res
        except:
            logging.exception(f'Request failed {res}')
            raise

    def _get_last_address_id(self):
        return int(self.get(constants.LAST_ADDRESS_ID_URL)[0]['id'])

    def _get_order_list(self):
        return self.get(constants.ORDER_LIST_URL)['content']

    def _get_last_order(self):
        order_list = self._get_order_list()
        return order_list[0] if order_list else None

    def _get_last_order_id(self):
        return int(self.last_order['customerOrderId']) if self.last_order else None

    def _get_products(self):
        order_lines = '+'.join([order_item['lineNumber'] for order_item in self.last_order['orderLines'] if self.last_order])
        return self.get(constants.PRODUCT_LIST_URL.format(order_lines)) if order_lines else {}

    def convert_order_list_to_dict(self):
        res = {}
        for ol in self.last_order['orderLines']:
            res[ol['lineNumber']] = ol
        return res

    def merge_last_order_to_basket(self):
        res = []
        last_order_dict = self.convert_order_list_to_dict()
        for p in self._get_products()['products']:
            pl = dict(canSubstitute='false',
                      lineNumber=str(p['lineNumber']),
                      productId=str(p['id']),
                      quantity=last_order_dict[str(p['lineNumber'])]['quantity'],
                      reservedQuantity=0,
                      trolleyItemId=-1)
            res.append(pl)

        items = self.patch(constants.TROLLEY_ITEMS_URL.format(self.customerOrderId), res) if res else None

        # if there is no match the dict will contain 'message' key with the details what's wrong
        if items and 'message' in items:
            raise ValueError(items['message'])
        else:
            return items

    def _get_payment_cards(self):
        return self.get(constants.PAYMENTS_CARDS_URL)

    def checkout_order(self, card_id: int, cvv: int):
        param = {"addressId": str(self.last_address_id),
                 "cardSecurityCode": str(cvv)}
        res = self.put(constants.CHECKOUT_URL.format(self.customerOrderId, card_id), param)
        return res['code']


class Slot:
    def __init__(self, session: Session, fulfilment_type: str, postcode: str):
        self.session = session
        self.fulfilment_type = fulfilment_type
        self.postcode = postcode

    def get_slots(self, branch_id: int, date_from: datetime):
        variables = {"slotDaysInput": {
            "branchId": str(branch_id),
            "slotType": self.fulfilment_type,
            "customerOrderId": str(self.session.customerOrderId),
            "addressId": str(self.session.last_address_id),
            "fromDate": date_from.strftime('%Y-%m-%d'),
            "size": 5
        }}

        slots_json = self.session.execute(constants.SLOT_QUERY, variables)

        return slots_json['data']['slotDays']['content'] if slots_json is not None else None

    def get_available_slots(self, branch_id: int = 753, page_cnt: int = 4):
        res = {}
        # the number of pages, each page contains 5 days, sometimes only 2 pages available on waitrose website
        for si in range(page_cnt):
            # get all slots for the necessary interval of time
            slot_days = self.get_slots(branch_id=branch_id, date_from=datetime.today() + timedelta(si*5))
            # loop through all slot days
            if slot_days:
                for sd in slot_days:
                    # go trough the all slots for the day and add only available ones to res
                    for s in sd['slots']:
                        if s['slotStatus'] not in ('FULLY_BOOKED', 'UNAVAILABLE'):
                            res[s['slotId']] = s
        return res

    def book_slot(self,
                  branch_id: int,
                  postcode: str,
                  address_id: int,
                  slot_type: str,
                  start_date_time: datetime,
                  end_date_time: datetime):
        variables = {"bookSlotInput": {
            "branchId": str(branch_id),
            "slotType": slot_type,
            "customerOrderId": str(self.session.customerOrderId),
            "customerId": str(self.session.customerId),
            "postcode": postcode,
            "addressId": str(address_id),
            "startDateTime": start_date_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
            "endDateTime": end_date_time.strftime('%Y-%m-%dT%H:%M:%SZ')}
        }

        book_res = self.session.execute(constants.BOOK_SLOT_QUERY, variables)

        failures = book_res['data']['bookSlot']['failures']
        if not failures or isinstance(failures, str) and failures.lower() == 'null':
            return True
        else:
            raise ValueError(f'Booking failed, see the details: {failures}')

    def get_current_slot(self):
        variables = {"currentSlotInput": {
            "customerOrderId": str(self.session.customerOrderId),
            "customerId": str(self.session.customerId)}
        }

        current_slot = self.session.execute(constants.CURRENT_SLOT_QUERY, variables)

        try:
            return current_slot['data']['currentSlot']['startDateTime'], \
                   current_slot['data']['currentSlot']['endDateTime']
        except:
            return None, None

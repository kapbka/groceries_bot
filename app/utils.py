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
        self.headers = {'authorization': f"Bearer {self.token}"}

        self.customerId = int(data['data']['generateSession']['customerId'])
        self.customerOrderId = int(data['data']['generateSession']['customerOrderId'])

        self.last_address_id = int(self.get_address_list()[0].get('id', -1))

        self.last_order = next(iter(self.get_order_dict().values()))
        self.last_order_id = int(self.last_order.get('customerOrderId', -1))

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
        else:
            return items

    def is_trolley_empty(self):
        r = requests.get(constants.PRODUCT_LIST_URL.format(self.customerOrderId), headers=self.headers).json()
        return len(r['trolley']['trolleyItems']) == 0

    def get_payment_card_list(self):
        return requests.get(constants.PAYMENTS_CARDS_URL, headers=self.headers).json()

    def get_card_id(self, card_num: int):
        cards = self.get_payment_card_list()
        for card in cards:
            if card['maskedCardNumber'].endswith(str(card_num)):
                return card['id']

    def checkout_trolley(self, card_id: int, cvv: int):
        param = {"addressId": str(self.last_address_id),
                 "cardSecurityCode": str(cvv)}

        res = requests.put(constants.CHECKOUT_URL.format(self.customerOrderId, card_id),
                           headers=self.headers, json=param).json()
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
                    # go trough all the slots for the day and add only available ones to res
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

    def book_first_available_slot(self,
                                  slots: dict,
                                  branch_id: int,
                                  postcode: str,
                                  address_id: int,
                                  slot_type: str):
        sd, ed = None, None

        for cur_slot in slots.values():
            sd = cur_slot['startDateTime']
            ed = cur_slot['endDateTime']

            try:
                book = self.book_slot(branch_id=branch_id,
                                      postcode=postcode,
                                      address_id=address_id,
                                      slot_type=slot_type,
                                      start_date_time=datetime.strptime(sd, '%Y-%m-%dT%H:%M:%SZ'),
                                      end_date_time=datetime.strptime(ed, '%Y-%m-%dT%H:%M:%SZ'))
                print(f'The slot "{sd} - {ed}" has been SUCCESSFULLY booked')
                break
            except:
                sd, ed = None, None
                logging.exception(f'Booking for the slot "{sd} - {ed}" failed, trying to book the next slot')
                continue

        if sd and ed:
            # slot has been booked
            return sd, ed
        else:
            raise ValueError('Failed to book all available slots')

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

import requests
from python_graphql_client import GraphqlClient
from datetime import datetime, timedelta
from app import constants
import logging
import typing


class Session:
    def __init__(self, login: str, password: str, query: str, end_point: str):
        self.login = login
        self.password = password
        self.client = GraphqlClient(endpoint=end_point)
        self.query = query
        self.end_point = end_point

        data = self.client.execute(
            query=query,
            variables={"session": {"username": login, "password": password, "customerId": "-1", "clientId": "WEB_APP"}}
        )
        self.token = data['data']['generateSession']['accessToken']
        self.customerId = data['data']['generateSession']['customerId']
        self.customerOrderId = data['data']['generateSession']['customerOrderId']


class Slot:
    def __init__(self, session: Session, fulfilment_type: str, postcode: str):
        self.session = session
        self.fulfilment_type = fulfilment_type
        self.postcode = postcode

    def get_branches(self):
        r = requests.get(
            f'https://www.waitrose.com/api/branch-prod/v3/branches?fulfilment_type=${self.fulfilment_type}&location=${self.postcode}',
            headers={'authorization': f"Bearer {self.session.token}"}
        )
        return r.content

    def get_last_address_id(self):
        r = requests.get(
            'https://www.waitrose.com/api/address-prod/v1/addresses?sortBy=-lastDelivery',
            headers={'authorization': f"Bearer {self.session.token}"}
        ).json()
        return r[0]['id']

    def get_slots(self, branch_id: int, date_from: datetime):
        variables = {"slotDaysInput": {
            "branchId": str(branch_id),
            "slotType": self.fulfilment_type,
            "customerOrderId": self.session.customerOrderId,
            "addressId": self.get_last_address_id(),
            "fromDate": date_from.strftime('%Y-%m-%d'),
            "size": 5
        }}

        slots_json = self.session.client.execute(
            query=constants.SLOT_QUERY,
            variables=variables,
            headers={'authorization': f"Bearer {self.session.token}"}
        )

        return slots_json['data']['slotDays']['content']

    def get_available_slots(self, branch_id: int = 753, page_cnt: int = 4):
        res = {}
        # the number of pages, each page contains 5 days, sometimes only 2 pages available on waitrose website
        for si in range(page_cnt):
            # get all slots for the necessary interval of time
            slot_days = self.get_slots(branch_id=branch_id, date_from=datetime.today() + timedelta(si*5))
            # loop through all slot days
            for sd in slot_days:
                # go trough all slots for the day and add only available ones to res
                for s in sd['slots']:
                    if s['slotStatus'] not in ('FULLY_BOOKED', 'UNAVAILABLE'):
                        res[s['slotId']] = s
        return res

    def book_slot(self, branch_id: int, postcode: str, address_id: int, slot_type: str, start_date_time: datetime, end_date_time: datetime):
        variables = {"bookSlotInput": {
            "branchId": str(branch_id),
            "slotType": slot_type,
            "customerOrderId": self.session.customerOrderId,
            "customerId": self.session.customerId,
            "postcode": postcode,
            "addressId": str(address_id),
            "startDateTime": start_date_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
            "endDateTime": end_date_time.strftime('%Y-%m-%dT%H:%M:%SZ')}
        }

        try:
            book_res = self.session.client.execute(query=constants.BOOK_SLOT_QUERY,
                                                   variables=variables,
                                                   headers={'authorization': f"Bearer {self.session.token}"})
            return book_res['data']['bookSlot']['failures'].lower() == 'null'
        # if any exception then log and return false
        except:
            logging.exception("Booking failed")
            return False

    def confirm_slot(self):
        variables = {"currentSlotInput": {
            "customerOrderId": self.session.customerOrderId,
            "customerId": self.session.customerId}
        }

        try:
            confirm_res = self.session.client.execute(query=constants.CONFIRM_SLOT_QUERY, variables=variables,
                                                      headers={'authorization': f"Bearer {self.session.token}"})
            return len(confirm_res['data']['currentSlot']) > 0
        # if any exception then log and return false
        except:
            logging.exception("Confirmation failed")
            return False

    def get_last_order_id(self):
        pass

    def add_last_order_to_basket(self):
        pass

    def save_order(self):
        pass

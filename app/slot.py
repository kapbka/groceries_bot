from datetime import datetime, timedelta
import logging
from app import constants
from session import Session


SUN, MON, TUE, WED, THU, FRI, SAT = range(7)


class Slot:
    def __init__(self, session: Session, slot_type: str):
        self.session = session
        self.slot_type = slot_type

    def get_slots(self, branch_id: int, date_from: datetime):
        variables = {"slotDaysInput": {
            "branchId": str(branch_id),
            "slotType": self.slot_type,
            "customerOrderId": str(self.session.customerOrderId),
            "addressId": str(self.session.last_address_id),
            "fromDate": date_from.strftime('%Y-%m-%d'),
            "size": 5
        }}

        slots_json = self.session.execute(constants.SLOT_QUERY, variables)

        return slots_json['data']['slotDays']['content'] if slots_json is not None else None

    def get_available_slots(self, slot_filter=None, page_cnt: int = 4):
        res = {}
        # the number of pages, each page contains 5 days, sometimes only 2 pages available on waitrose website
        for si in range(page_cnt):
            # get all slots for the necessary interval of time
            slot_days = self.get_slots(branch_id=self.session.default_branch_id, date_from=datetime.today() + timedelta(si*5))
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

    def book_first_available_slot(self):
        available_slots = self.get_available_slots()
        sd, ed = None, None

        for cur_slot in available_slots.values():
            sd = cur_slot['startDateTime']
            ed = cur_slot['endDateTime']

            try:
                book = self.book_slot(branch_id=self.session.default_branch_id,
                                      postcode=self.session.default_postcode,
                                      address_id=self.session.default_address_id,
                                      slot_type=self.slot_type,
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
            raise ValueError('Failed to book each of available slots')

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

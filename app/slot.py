from datetime import datetime, timedelta, time
import logging
from app import constants
from app.session import Session
from enum import IntEnum


WEEKDAYS = IntEnum('Weekdays', 'mon tue wed thu fri sat sun', start=0)


class Slot:
    def __init__(self, session: Session, slot_type: str):
        self.session = session
        self.slot_type = slot_type

    def get_slots(self, branch_id: int, date_from: datetime):
        variables = {"slotDaysInput": {
            "branchId": str(branch_id),
            "slotType": self.slot_type,
            "customerOrderId": str(self.session.customerOrderId),
            "addressId": str(self.session.default_address_id),
            "fromDate": date_from.strftime('%Y-%m-%d'),
            "size": 5
        }}

        slots_json = self.session.execute(constants.SLOT_QUERY, variables)

        return slots_json['data']['slotDays']['content']

    def get_available_slots(self, slot_filter: dict = None, page_cnt: int = 4):
        """
        Returns all available slots with filters if necessary
        :param slot_filter: list which contains tuples each of which contains 3 elements:
                            weekday, start slot time, end slot time:
                            {'fri': (datetime.time(16, 00, 00), datetime.time(20, 00, 00)),
                             'sun': (datetime.time(12, 00, 00), datetime.time(18, 00, 00))}
        :param page_cnt: the number of pages, each page contains 5 days, sometimes only 2 pages available on waitrose website
        :return: dict with slots
        """
        # slot filter validation
        if slot_filter:
            if not isinstance(slot_filter, dict):
                raise ValueError('slot_filter parameter must be a dict!')
            for k, v in slot_filter.items():
                if not isinstance(k, str) or k.lower() not in [e.name for e in WEEKDAYS]:
                    raise ValueError('Wrong work day, must be on of the work days: mon tue wed thu fri sat sun')
                if len(v) == 0:
                    raise ValueError(f'No slots passed for "{k}"')
                for t in v:
                    if not isinstance(t, time):
                        raise ValueError('A filter value must be time for dayweek {k}')

        res = {}
        for si in range(page_cnt):
            slot_days = self.get_slots(branch_id=self.session.default_branch_id, date_from=datetime.today() + timedelta(si*5))
            for sd in slot_days:
                sd_weekday = datetime.strptime(sd['date'], '%Y-%m-%d').weekday()
                sd_weekday = WEEKDAYS(sd_weekday).name
                if not slot_filter or sd_weekday in list(slot_filter.keys()):
                    res.update({s['slotId']: s for s in sd['slots']
                                if s['slotStatus'] not in ['FULLY_BOOKED', 'UNAVAILABLE']
                                and
                                (not slot_filter
                                 or
                                 datetime.strptime(s['startDateTime'], '%Y-%m-%dT%H:%M:%SZ').time() in
                                 slot_filter[sd_weekday])
                              })
                else:
                    continue

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

        if not sd and not ed:
            raise ValueError('Failed to book each of available slots')

        return sd, ed

    def get_current_slot(self):
        variables = {"currentSlotInput": {
            "customerOrderId": str(self.session.customerOrderId),
            "customerId": str(self.session.customerId)}}

        current_slot = self.session.execute(constants.CURRENT_SLOT_QUERY, variables)

        try:
            return current_slot['data']['currentSlot']['startDateTime'], \
                   current_slot['data']['currentSlot']['endDateTime']
        except:
            return None, None

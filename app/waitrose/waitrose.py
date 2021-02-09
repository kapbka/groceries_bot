# Waitrose class
from app.waitrose.session import Session
from app.waitrose.slot import Slot
from app.constants import CHAIN_INTERVAL_HRS
from app.timed_lru_cache import timed_lru_cache
import datetime

SLOT_EXPIRY_SEC = 60


class Waitrose:

    name = 'waitrose'
    display_name = 'Waitrose'

    session_expiry_sec = 300

    slot_start_time = datetime.time(7, 00, 00)
    slot_end_time = datetime.time(22, 00, 00)
    slot_interval_hrs = CHAIN_INTERVAL_HRS

    def __init__(self, login, password):
        self.login = login
        self.password = password
        self.slot_filter = None
        self.session = Session(login, password)

    @timed_lru_cache(SLOT_EXPIRY_SEC)
    def get_slots(self, slot_type='DELIVERY'):
        return Slot(session=self.session, slot_type=slot_type).get_available_slots()

    def book(self, start_datetime):
        slot = Slot(session=self.session, slot_type='DELIVERY')
        return slot.book_slot_default_address('DELIVERY', start_datetime,
                                              start_datetime + datetime.timedelta(hours=self.slot_interval_hrs))

    def book_current_or_first_available_slot(self, slot_type='DELIVERY'):
        slot = Slot(session=self.session, slot_type=slot_type)

        start_date = slot.get_current_slot()

        # if there is no current booked slot
        if not start_date:
            start_date, end_date = slot.book_first_available_slot()

    def checkout(self, cvv):
        res = None
        # if a trolley is empty will try to fill it in with items from the last order
        if self.session.is_trolley_empty():
            self.session.merge_last_order_to_trolley()

        # if cvv is passed proceed with checkout not to lose the slot
        if self.cvv:
            card_list = self.session.get_payment_card_list()
            # TODO: exception if card_list is empty
            res = self.session.checkout_trolley(self.session.customerOrderId, card_list[0], cvv)
        return str(self.session.customerOrderId)

    def get_current_slot(self):
        slot = Slot(session=self.session, slot_type='DELIVERY')
        return slot.get_current_slot()

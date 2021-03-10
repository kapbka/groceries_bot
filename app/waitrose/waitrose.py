# Waitrose class
from app.waitrose.session import Session
from app.waitrose.slot import Slot
from app.constants import CHAIN_INTERVAL_HRS
from app.timed_lru_cache import timed_lru_cache
import datetime
from app.log import app_exception

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
        slot = Slot(session=self.session, slot_type=slot_type)
        return slot.get_available_slots()

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
        curr_slot = self.get_current_slot()
        if self.session.order_exists(curr_slot):
            raise app_exception.OrderExistsException

        if not cvv:
            raise ValueError('Empty cvv!')

        # if a trolley is empty will try to fill it in with items from the last order
        if self.session.is_trolley_empty():
            self.session.merge_last_order_to_trolley()

        card_list = self.session.get_payment_card_list()
        self.session.checkout_trolley(int(card_list[0]['id']), cvv)
        return str(self.session.customerOrderId)

    def get_current_slot(self):
        slot = Slot(session=self.session, slot_type='DELIVERY')
        return slot.get_current_slot()

    def get_last_order_date(self):
        return self.session.get_last_order_date()

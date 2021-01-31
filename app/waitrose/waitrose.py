# Waitrose class
from app.waitrose.session import Session
from app.waitrose.slot import Slot
import datetime


class Waitrose:

    slot_start_time = datetime.time(7, 00, 00)
    slot_end_time = datetime.time(22, 00, 00)

    def __init__(self, login, password, slot_filter=None, cvv=None):
        self.login = login
        self.password = password
        self.slot_filter = slot_filter
        self.cvv = cvv
        self.session = Session(login, password)

    def get_all_available_slots(self, slot_type='DELIVERY'):
        return Slot(session=self.session, slot_type=slot_type).get_available_slots()

    def book_slot_default_address(self, slot_type, start_datetime, end_datetime):
        slot = Slot(session=self.session, slot_type=slot_type)
        return slot.book_slot_default_address(slot_type, start_datetime, end_datetime)

    def book_current_or_first_available_slot(self, slot_type='DELIVERY'):
        slot = Slot(session=self.session, slot_type=slot_type)

        start_date, end_date = slot.get_current_slot()

        # if there is no current booked slot
        if not start_date and not end_date:
            start_date, end_date = slot.book_first_available_slot()

    def checkout_trolley(self):
        # if a trolley is empty will try to fill it in with items from the last order
        if self.session.is_trolley_empty():
            self.session.merge_last_order_to_trolley()

        # if cvv is passed proceed with checkout not to lose the slot
        if self.cvv:
            card_list = self.session.get_payment_card_list()
            self.session.checkout_trolley(self.session.customerOrderId, card_list[0], self.cvv)

    def get_current_slot(self):
        slot = Slot(session=self.session, slot_type='DELIVERY')
        return slot.get_current_slot()

from session import Session
from slot import Slot


class Waitrose:
    def __init__(self, login, password, slot_filter=None, cvv=None):
        self.login = login
        self.password = password
        self.slot_filter = slot_filter
        self.cvv = cvv
        self.session = Session(login, password)

    def book_slot(self, slot_type='DELIVERY'):
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

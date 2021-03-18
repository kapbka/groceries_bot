# Slot Menu classes

import logging
from datetime import datetime
from app.bot.telegram import constants
from app.bot.telegram.settings import Settings
from app.bot.telegram.menu.menu import Menu, HelpMenu
from app.bot.telegram.helpers import get_chain_instance, get_pretty_slot_day_name, get_pretty_slot_name, \
    get_pretty_slot_time_name
from app.log.status_bar import ProgressBarWriter
from app.bot.telegram.helpers import asynchronous


class SlotsMenu(Menu):
    def __init__(self, chat_id, chain_cls, display_name: str, make_book: bool = True, make_checkout: bool = False):
        super().__init__(chat_id, chain_cls, display_name, [])
        self.make_book = make_book
        self.make_checkout = make_checkout

    def _generate_children(self, message):
        logging.debug(f'self.display_name {self.display_name}')

        with ProgressBarWriter(message) as _:
            # 1. getting slots
            chain = get_chain_instance(message.chat_id, self.chain_cls)

            slots = chain.get_slots()

            # 2. then we register children
            slot_day = None
            children = []
            for i, sd in enumerate(slots):
                if i == 0 or slot_day != sd.date():
                    slot_day = sd.date()
                    m_day = SlotDayMenu(self.chat_id, self.chain_cls, slot_day, get_pretty_slot_day_name(slot_day),
                                        self.make_book, self.make_checkout)
                    m_day.parent = self
                    m_day.register(self.bot)
                    children.append(m_day)

            # 3. add Help menu
            m_help = HelpMenu(self.chat_id, self.chain_cls, constants.M_HELP, [])
            m_help.parent = self
            m_help.register(self.bot)
            children.append(m_help)

            for child in self.children:
                child.unregister()
            self.children = children

    @asynchronous
    def create(self, message):
        self._generate_children(message)
        message.reply_text(self.display_name, reply_markup=self._keyboard(self.children))

    @asynchronous
    def display(self, message):
        self._generate_children(message)
        message.edit_text(self.display_name, reply_markup=self._keyboard(self.children))

    def help(self):
        if self.make_checkout:
            return constants.H_BOOK_CHECKOUT
        else:
            return constants.H_BOOK


class SlotDayMenu(Menu):
    def __init__(self, chat_id, chain_cls, slot_day: datetime.date, display_name: str,
                 make_book: bool = True, make_checkout: bool = False):
        super().__init__(chat_id, chain_cls, display_name, [], 21)
        self.slot_day = slot_day
        self.make_book = make_book
        self.make_checkout = make_checkout

    @asynchronous
    def display(self, message):
        logging.debug(f'self.display_name {self.display_name}')

        with ProgressBarWriter(message) as _:
            # 1. getting slots
            chain = get_chain_instance(message.chat_id, self.chain_cls)
            slots = chain.get_slots()
            cur_slot = chain.get_current_slot()

            # 2. then we register children
            children = []
            for i, sd in enumerate(slots):
                if sd.date() == self.slot_day:
                    slot_disp_name = get_pretty_slot_time_name(sd, self.chain_cls)
                    if sd == cur_slot:
                        slot_disp_name = constants.ENABLED_EMOJI + slot_disp_name
                    m_slot = SlotTimeMenu(self.chat_id, self.chain_cls, slot_disp_name, chain, sd, self.make_book, self.make_checkout)
                    m_slot.parent = self
                    m_slot.register(self.bot)
                    children.append(m_slot)

            for child in self.children:
                child.unregister()
            self.children = children

        # 3. adding text
        message.edit_text(self.display_name, reply_markup=self._keyboard(self.children))


class SlotTimeMenu(Menu):
    def __init__(self, chat_id, chain_cls, display_name: str, chain, start_datetime: datetime,
                 make_book: bool, make_checkout: bool):
        super().__init__(chat_id, chain_cls, display_name, [], 23)
        self.chain = chain
        self.start_datetime = start_datetime
        if not make_book and not make_checkout:
            raise ValueError(constants.E_NO_ACTION)
        self.make_book = make_book
        self.make_checkout = make_checkout

    @asynchronous
    def display(self, message):
        logging.debug(f'self.display_name {self.display_name}')

        with ProgressBarWriter(message) as _:
            endings = []
            if self.make_book:
                self.chain.book(self.start_datetime)
                endings.append(constants.S_BOOKED)
            if self.make_checkout:
                res = self.chain.checkout(Settings(message.chat_id, self.chain_cls.name).cvv)
                endings.append(f'{constants.S_CHECKED_OUT}. {constants.S_ORDER_NUMBER} {res}')

        disp_name = f"Slot {get_pretty_slot_name(self.start_datetime, self.chain_cls)} has been {' and '.join(endings)}"
        message.edit_text(disp_name, reply_markup=self._keyboard([]))

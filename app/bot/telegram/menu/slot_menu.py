# Slot Menu classes

import logging
from telegram import Message
from datetime import datetime, timedelta
from app.bot.telegram.constants import ENABLED_EMOJI
from app.bot.telegram.creds import Creds
from app.constants import WEEKDAYS
from app.bot.telegram.menu.menu import Menu
from app.bot.telegram.chat_chain_cache import ChatChainCache
from logging import StreamHandler


class ResponseLogger(StreamHandler):
    def __init__(self, message: Message):
        StreamHandler.__init__(self)
        self.message = message
        self.setLevel(logging.INFO)

    def emit(self, record):
        txt = self.format(record)
        self.message.edit_text(self.message.text + ': ' + txt, reply_markup=self.message.reply_markup)


class SlotDayMenu(Menu):
    def __init__(self, chain_cls, display_name: str, make_book: bool=True, make_checkout: bool=False):
        super().__init__(chain_cls, display_name, [])
        self.make_book = make_book
        self.make_checkout = make_checkout

    def display(self, message):
        logging.debug(f'self.display_name {self.display_name}')

        # 1. getting slots
        chat_id = message.chat_id
        chain = ChatChainCache.create_or_get(chat_id, self.chain_cls,
                                             Creds.chat_creds[chat_id][self.chain_cls.name].login,
                                             Creds.chat_creds[chat_id][self.chain_cls.name].password)

        log = logging.getLogger('telegram')
        log.setLevel(logging.INFO)
        ch = ResponseLogger(message)
        ch.setFormatter(logging.Formatter('%(message)s'))
        log.addHandler(ch)
        slots = chain.get_slots()

        cur_slot = chain.get_current_slot()

        # 2. then we register children
        self.children.clear()
        slot_day = None
        for i, sd in enumerate(slots):
            if i == 0 or slot_day != sd.date():
                slot_day = sd.date()
                day_disp_name = f"{slot_day.day}-{slot_day.strftime('%B')[0:3]} " \
                            f"{str(WEEKDAYS(slot_day.weekday()).name).capitalize()}"
                m_day = Menu(self.chain_cls, day_disp_name, [])
                m_day.parent = self
                # append m_day as a child to Show available slots menu
                self.children.append(m_day)
                m_day.register(self.bot)

            # create slot menu with slot start and end time
            ss_time = sd
            se_time = sd + timedelta(hours=self.chain_cls.slot_interval_hrs)
            slot_disp_name = "{:02d}:{:02d}-{:02d}:{:02d}".format(ss_time.hour, ss_time.minute, se_time.hour, se_time.minute)
            if cur_slot == sd:
                slot_disp_name = ENABLED_EMOJI + slot_disp_name
            m_slot = SlotTimeMenu(self.chain_cls, slot_disp_name, chain, ss_time, self.make_book, self.make_checkout)
            m_slot.parent = self.children[-1]
            # append m_slot as a child to m_day menu
            self.children[-1].children.append(m_slot)
            m_slot.register(self.bot)

        # 3. adding text
        message.edit_text(self.display_name, reply_markup=self._keyboard(self.children))


class SlotTimeMenu(Menu):
    def __init__(self, chain_cls, display_name: str, chain, start_datetime: datetime,
                 make_book: bool, make_checkout: bool, alignment_len: int = 40):
        super().__init__(chain_cls, display_name, [], alignment_len)
        self.chain = chain
        self.start_datetime = start_datetime
        if not make_book and not make_checkout:
            raise ValueError('At least one action required: booking or checkout!')
        self.make_book = make_book
        self.make_checkout = make_checkout

    def display(self, message):
        logging.debug(f'self.display_name {self.display_name}')

        endings = []

        if self.make_book:
            self.chain.book(self.start_datetime)
            endings.append('booked')

        if self.make_checkout:
            self.chain.checkout(Creds.chat_creds[message.chat_id][self.chain_cls.name].cvv)
            endings.append('checked out')

        disp_name = f"Slot {self.display_name} has been {' and '.join(endings)}"

        message.edit_text(disp_name, reply_markup=self._keyboard([]))

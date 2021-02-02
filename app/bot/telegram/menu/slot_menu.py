# Slot Menu classes

import logging
from datetime import datetime, timedelta
from app.bot.telegram.creds import Creds
from app.constants import WEEKDAYS
from app.bot.telegram.menu.menu import Menu
from app.bot.telegram.chat_chain_cache import ChatChainCache


class SlotDayMenu(Menu):
    def __init__(self, chain_cls, display_name: str):
        super().__init__(chain_cls, display_name, [])

    def display(self, message):
        logging.debug(f'self.display_name {self.display_name}')

        # 1. getting slots
        chat_id = message.chat_id
        chain = ChatChainCache.create_or_get(chat_id, self.chain_cls,
                                             Creds.chat_creds[chat_id][self.chain_cls.name].login,
                                             Creds.chat_creds[chat_id][self.chain_cls.name].password,
                                             Creds.chat_creds[chat_id][self.chain_cls.name].cvv)
        slots = chain.get_slots()

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
            m_slot = SlotTimeMenu(self.chain_cls, slot_disp_name, chain, ss_time)
            m_slot.parent = self.children[-1]
            # append m_slot as a child to m_day menu
            self.children[-1].children.append(m_slot)
            m_slot.register(self.bot)

        # 3. adding text
        message.edit_text(self.display_name, reply_markup=self._keyboard(self.children))


class SlotTimeMenu(Menu):
    def __init__(self, chain_cls, display_name: str, chain, start_datetime: datetime, alignment_len: int = 40):
        super().__init__(chain_cls, display_name, [], alignment_len)
        self.chain = chain
        self.start_datetime = start_datetime

    def display(self, message):
        logging.debug(f'self.display_name {self.display_name}')
        # slot booking
        self.chain.book(self.start_datetime)

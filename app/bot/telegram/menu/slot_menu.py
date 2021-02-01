# Slot Menu classes

import logging
from datetime import datetime
from app.bot.telegram.creds import Creds
from app.constants import WEEKDAYS
from app.waitrose.waitrose import Waitrose
from app.bot.telegram.menu.menu import Menu


class SlotDayMenu(Menu):
    def __init__(self, chain_cls, display_name: str):
        super().__init__(chain_cls, display_name, [])

    def display(self, message):
        logging.debug(f'self.display_name {self.display_name}')

        # 1. getting slots
        chat_id = message.chat_id
        chain = self.chain_cls(Creds.chat_creds[chat_id][self.chain_cls.name].login,
                               Creds.chat_creds[chat_id][self.chain_cls.name].password)
        all_slots = chain.get_all_available_slots()

        # 2. then we register children
        self.children.clear()
        slot_day = None
        for i, s in enumerate(all_slots.values()):
            if i == 0 or slot_day != datetime.strptime(s['startDateTime'], '%Y-%m-%dT%H:%M:%SZ').date():
                slot_day = datetime.strptime(s['startDateTime'], '%Y-%m-%dT%H:%M:%SZ').date()
                day_disp_name = f"{slot_day.day}-{slot_day.strftime('%B')[0:3]} " \
                            f"{str(WEEKDAYS(slot_day.weekday()).name).capitalize()}"
                m_day = Menu(self.chain_cls, day_disp_name, [])
                m_day.parent = self
                # append m_day as a child to Show available slots menu
                self.children.append(m_day)
                m_day.register(self.bot)

            # create slot menu
            slot_start_datetime = datetime.strptime(s['startDateTime'], '%Y-%m-%dT%H:%M:%SZ')
            slot_end_datetime = datetime.strptime(s['endDateTime'], '%Y-%m-%dT%H:%M:%SZ')
            slot_disp_name = "{:02d}:{:02d}-{:02d}:{:02d}".format(slot_start_datetime.hour, slot_start_datetime.minute,
                                                                  slot_end_datetime.hour, slot_end_datetime.minute)
            m_slot = SlotTimeMenu(self.chain_cls, slot_disp_name, chain, slot_start_datetime, slot_end_datetime)
            m_slot.parent = self.children[-1]
            # append m_slot as a child to m_day menu
            self.children[-1].children.append(m_slot)
            m_slot.register(self.bot)

        # 3. adding text
        message.edit_text(self.display_name, reply_markup=self._keyboard(self.children))


class SlotTimeMenu(Menu):
    def __init__(self, chain_cls, display_name: str, chain, start_datetime: datetime, end_datetime: datetime,
                 alignment_len: int = 40):
        super().__init__(chain_cls, display_name, [], alignment_len)
        self.chain = chain
        self.start_datetime = start_datetime
        self.end_datetime = end_datetime

    def display(self, message):
        logging.debug(f'self.display_name {self.display_name}')
        # slot booking
        self.chain.book_slot_default_address('DELIVERY', self.start_datetime, self.end_datetime)

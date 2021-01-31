# Filter Menu classes

import logging
from datetime import datetime
from app.constants import WEEKDAYS
from app.bot.telegram.constants import ENABLED_EMOJI, DISABLED_EMOJI
from app.bot.telegram.menu.menu import Menu
from app.bot.telegram.autobook import Autobook


class FilterDayMenu(Menu):
    def __init__(self, chain_name: str, display_name: str, start_time: datetime.time, end_time: datetime.time):
        super().__init__(chain_name, display_name, [])
        self.start_time = start_time
        self.end_time = end_time

    def display(self, message):
        logging.debug(f'self.display_name {self.display_name}')

        self.init_autobook(message)

        self.children.clear()

        # 1. create filter day of week
        for wd in range(7):
            m_filter_day = Menu(self.chain_name, f'{str(WEEKDAYS(wd).name).capitalize()}', [])
            m_filter_day.parent = self
            # append m_day as a child to Show available slots menu
            self.children.append(m_filter_day)
            m_filter_day.register(self.bot)

            # 2. create slots for the day of the week
            for st in range(self.start_time.hour, self.end_time.hour):
                wd_filters = getattr(Autobook.chat_autobook[message.chat_id][self.chain_name], WEEKDAYS(wd).name)
                slot_name = "{:02d}:00-{:02d}:00".format(st, st+1)
                if slot_name in wd_filters:
                    slot_prefix = ENABLED_EMOJI
                else:
                    slot_prefix = DISABLED_EMOJI
                m_filter_slot = FilterTimeMenu(self.chain_name, "{} {}".format(slot_prefix, slot_name))
                m_filter_slot.parent = self.children[-1]
                # append m_slot as a child to m_day menu
                self.children[-1].children.append(m_filter_slot)
                m_filter_slot.register(self.bot)

        if Autobook.chat_autobook[message.chat_id][self.chain_name].autobook:
            enabled_prefix = ENABLED_EMOJI
        else:
            enabled_prefix = DISABLED_EMOJI
        m_auto_booking = EnabledMenu(self.chain_name, f'{enabled_prefix} Enabled')
        m_auto_booking.parent = self
        # append m_day as a child to Show available slots menu
        self.children.append(m_auto_booking)
        m_auto_booking.register(self.bot)

        # 3. adding text
        message.edit_text(self.display_name, reply_markup=self._keyboard(self.children))

    def init_autobook(self, message):
        if message.chat_id not in Autobook.chat_autobook or self.chain_name not in Autobook.chat_autobook[message.chat_id]:
            Autobook.chat_autobook[message.chat_id] = {self.chain_name: Autobook(message.chat_id, self.chain_name)}


class FilterTimeMenu(Menu):
    def __init__(self, chain_name: str, display_name: str, alignment_len: int = 40):
        super().__init__(chain_name, display_name, [], alignment_len)

    def display(self, message):
        wd = self.parent.display_name.lower()
        wd_filters = getattr(Autobook.chat_autobook[message.chat_id][self.chain_name], wd)
        if self.display_name.startswith(ENABLED_EMOJI):
            # remove
            wd_filters.remove(self.display_name[2:])
            self.display_name = self.display_name.replace(ENABLED_EMOJI, DISABLED_EMOJI)
        else:
            # add
            wd_filters.append(self.display_name[2:])
            self.display_name = self.display_name.replace(DISABLED_EMOJI, ENABLED_EMOJI)
        setattr(Autobook.chat_autobook[message.chat_id][self.chain_name], wd, wd_filters)
        self.parent.display(message)


class EnabledMenu(Menu):
    def __init__(self, chain_name: str, display_name: str, alignment_len: int = 10):
        super().__init__(chain_name, display_name, [], alignment_len)

    def display(self, message):
        if self.display_name.startswith(ENABLED_EMOJI):
            # remove
            Autobook.chat_autobook[message.chat_id][self.chain_name].autobook = False
            self.display_name = self.display_name.replace(ENABLED_EMOJI, DISABLED_EMOJI)
        else:
            # add
            Autobook.chat_autobook[message.chat_id][self.chain_name].autobook = True
            self.display_name = self.display_name.replace(DISABLED_EMOJI, ENABLED_EMOJI)
        self.parent.display(message)
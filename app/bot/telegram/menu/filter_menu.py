# Filter Menu classes

import logging
import datetime
from app.constants import WEEKDAYS
from telegram import Message
from app.bot.telegram.constants import ENABLED_EMOJI, DISABLED_EMOJI
from app.bot.telegram.menu.menu import Menu
from app.bot.telegram.menu.text_menu import CvvMenu
from app.bot.telegram.autobook import Autobook
from app.bot.telegram.creds import Creds


class FilterDayMenu(Menu):
    def __init__(self, chain_cls, display_name: str):
        super().__init__(chain_cls, display_name, [])

        self.start_time = chain_cls.slot_start_time
        self.end_time = chain_cls.slot_end_time

    def _generate(self, message):
        logging.debug(f'self.display_name {self.display_name}')

        self.init_autobook(message)

        self.children.clear()

        # 1. create filter day of week
        for wd in range(7):
            m_filter_day = Menu(self.chain_cls, f'{str(WEEKDAYS(wd).name).capitalize()}', [])
            m_filter_day.parent = self
            # append m_day as a child to Show available slots menu
            self.children.append(m_filter_day)
            m_filter_day.register(self.bot)

            # 2. create slots for the day of the week
            for st in range(self.start_time.hour, self.end_time.hour):
                wd_filters = getattr(Autobook.chat_autobook[message.chat_id][self.chain_cls.name], WEEKDAYS(wd).name)
                slot_name = "{:02d}:00-{:02d}:00".format(st, st+1)
                if slot_name in wd_filters:
                    slot_prefix = ENABLED_EMOJI
                else:
                    slot_prefix = DISABLED_EMOJI
                m_filter_slot = FilterTimeMenu(self.chain_cls, "{} {}".format(slot_prefix, slot_name))
                m_filter_slot.parent = self.children[-1]
                # append m_slot as a child to m_day menu
                self.children[-1].children.append(m_filter_slot)
                m_filter_slot.register(self.bot)

        if Autobook.chat_autobook[message.chat_id][self.chain_cls.name].autobook:
            enabled_prefix = ENABLED_EMOJI
        else:
            enabled_prefix = DISABLED_EMOJI
        m_auto_booking = EnabledMenu(self.chain_cls, f'{enabled_prefix} Enabled')
        m_auto_booking.parent = self
        # append m_day as a child to Show available slots menu
        self.children.append(m_auto_booking)
        m_auto_booking.register(self.bot)

    def create(self, message):
        self._generate(message)

        message.reply_text(self.display_name, reply_markup=self._keyboard(self.children))

    def display(self, message):
        self._generate(message)

        message.edit_text(self.display_name, reply_markup=self._keyboard(self.children))

    def init_autobook(self, message):
        if message.chat_id not in Autobook.chat_autobook or self.chain_cls.name not in Autobook.chat_autobook[message.chat_id]:
            Autobook.chat_autobook[message.chat_id] = {self.chain_cls.name: Autobook(message.chat_id, self.chain_cls.name)}


class FilterTimeMenu(Menu):
    def __init__(self, chain_cls, display_name: str, alignment_len: int = 40):
        super().__init__(chain_cls, display_name, [], alignment_len)

    def display(self, message):
        wd = self.parent.display_name.lower()
        wd_filters = getattr(Autobook.chat_autobook[message.chat_id][self.chain_cls.name], wd)
        if self.display_name.startswith(ENABLED_EMOJI):
            # remove
            wd_filters.remove(self.display_name[2:])
            self.display_name = self.display_name.replace(ENABLED_EMOJI, DISABLED_EMOJI)
        else:
            # add
            wd_filters.append(self.display_name[2:])
            self.display_name = self.display_name.replace(DISABLED_EMOJI, ENABLED_EMOJI)
        setattr(Autobook.chat_autobook[message.chat_id][self.chain_cls.name], wd, wd_filters)
        self.parent.display(message)


class EnabledMenu(Menu):
    def __init__(self, chain_cls, display_name: str, alignment_len: int = 10):
        super().__init__(chain_cls, display_name, [], alignment_len)

    def display(self, message: Message):
        is_cvv = Creds.chat_creds[message.chat_id][self.chain_cls.name].cvv

        Autobook.chat_autobook[message.chat_id][self.chain_cls.name].autobook = \
            not Autobook.chat_autobook[message.chat_id][self.chain_cls.name].autobook

        if self.display_name.startswith(DISABLED_EMOJI) and not is_cvv:
            m_cvv = CvvMenu(self.chain_cls, self.bot, 'Enable autobooking',
                            f'{self.chain_cls.display_name}/Enable autobooking: Please enter your cvv',
                            self.parent)
            m_cvv.register(self.bot)
            m_cvv.parent = self
            m_cvv.display(message)

        else:
            if self.display_name.startswith(ENABLED_EMOJI):
                self.display_name = self.display_name.replace(ENABLED_EMOJI, DISABLED_EMOJI)
            else:
                self.display_name = self.display_name.replace(DISABLED_EMOJI, ENABLED_EMOJI)
            self.parent.display(message)
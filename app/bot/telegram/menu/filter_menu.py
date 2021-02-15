# Filter Menu classes

import logging
from telegram.ext import CallbackQueryHandler
from app.constants import WEEKDAYS
from telegram import Message
from app.bot.telegram.constants import ENABLED_EMOJI, DISABLED_EMOJI
from app.bot.telegram.menu.menu import Menu
from app.bot.telegram.menu.text_menu import CvvMenu
from app.bot.telegram.autobook import Autobook
from app.bot.telegram.creds import Creds
from app.bot.telegram.helpers import get_message, get_pretty_filter_slot_time_name
from app.bot.telegram import constants
from app.bot.log.exception_handler import handle_exception


class FilterDaysMenu(Menu):
    def __init__(self, chain_cls, display_name: str):
        super().__init__(chain_cls, display_name, [])

    def _generate(self, message):
        logging.debug(f'self.display_name {self.display_name}')

        self.init_autobook(message)

        # 1. days of the week menus
        children = []
        for wd in range(7):
            m_filter_day = FilterDayMenu(self.chain_cls, f'{str(WEEKDAYS(wd).name).capitalize()}', wd)
            m_filter_day.parent = self
            m_filter_day.register(self.bot)
            children.append(m_filter_day)

        # 2. interval menu
        m_interval = IntervalMenu(self.chain_cls, f'{constants.M_MIN_ORDER_INTERVAL} (up to {Autobook.max_autobook_interval} days)')
        m_interval.parent = self
        m_interval.register(self.bot)
        children.append(m_interval)

        # 3. enable autobooking menu
        if Autobook.chat_autobook[message.chat_id][self.chain_cls.name].autobook:
            enabled_prefix = ENABLED_EMOJI
        else:
            enabled_prefix = DISABLED_EMOJI
        m_auto_booking = EnabledMenu(self.chain_cls, f'{enabled_prefix} {constants.M_ENABLED}')
        m_auto_booking.parent = self
        m_auto_booking.register(self.bot)
        children.append(m_auto_booking)

        # unregister if we need to redraw the menu
        for child in self.children:
            child.unregister()
        self.children = children

    def create(self, message):
        self._generate(message)

        message.reply_text(self.display_name, reply_markup=self._keyboard(self.children))

    def display(self, message):
        self._generate(message)

        message.edit_text(self.display_name, reply_markup=self._keyboard(self.children))

    def init_autobook(self, message):
        chat_id = message.chat_id
        if chat_id not in Autobook.chat_autobook or self.chain_cls.name not in Autobook.chat_autobook[chat_id]:
            Autobook.chat_autobook[chat_id] = {self.chain_cls.name: Autobook(chat_id, self.chain_cls.name)}


class FilterDayMenu(Menu):
    def __init__(self, chain_cls, display_name: str, week_day: int):
        super().__init__(chain_cls, display_name, [])

        self.week_day = week_day
        self.start_time = chain_cls.slot_start_time
        self.end_time = chain_cls.slot_end_time

    def _generate(self, message):
        logging.debug(f'self.display_name {self.display_name}')

        children = []
        for st in range(self.start_time.hour, self.end_time.hour):
            wd_filters = getattr(Autobook.chat_autobook[message.chat_id][self.chain_cls.name], WEEKDAYS(self.week_day).name)
            if st in wd_filters:
                slot_prefix = ENABLED_EMOJI
            else:
                slot_prefix = DISABLED_EMOJI
            slot_name = f'{slot_prefix} {get_pretty_filter_slot_time_name(st, self.chain_cls)}'
            m_filter_slot = FilterTimeMenu(self.chain_cls, slot_name, self.week_day, st)
            m_filter_slot.parent = self
            m_filter_slot.register(self.bot)
            children.append(m_filter_slot)

        for child in self.children:
            child.unregister()
        self.children = children

    def create(self, message):
        self._generate(message)

        message.reply_text(self.display_name, reply_markup=self._keyboard(self.children))

    def display(self, message):
        self._generate(message)

        message.edit_text(self.display_name, reply_markup=self._keyboard(self.children))


class FilterTimeMenu(Menu):
    def __init__(self, chain_cls, display_name: str, week_day: int, day_time: int, alignment_len: int = 40):
        super().__init__(chain_cls, display_name, [], alignment_len)

        self.week_day = week_day
        self.day_time = day_time

    def display(self, message):
        wd = WEEKDAYS(self.week_day).name
        wd_filters = getattr(Autobook.chat_autobook[message.chat_id][self.chain_cls.name], wd)
        if self.display_name.startswith(ENABLED_EMOJI):
            # remove
            wd_filters.remove(self.day_time)
            self.display_name = self.display_name.replace(ENABLED_EMOJI, DISABLED_EMOJI)
        else:
            # add
            wd_filters.append(self.day_time)
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
            m_cvv = CvvMenu(self.chain_cls, self.bot, constants.M_ENABLE_AUTOBOOKING,
                            f'{self.chain_cls.display_name}/{constants.M_ENABLE_AUTOBOOKING}: {constants.S_CVV}')
            m_cvv.register(self.bot)
            m_cvv.parent = self
            m_cvv.next_menu = self.parent
            m_cvv.display(message)
        else:
            if self.display_name.startswith(ENABLED_EMOJI):
                self.display_name = self.display_name.replace(ENABLED_EMOJI, DISABLED_EMOJI)
            else:
                self.display_name = self.display_name.replace(DISABLED_EMOJI, ENABLED_EMOJI)
            self.parent.display(message)


class IntervalMenu(Menu):
    def __init__(self, chain_cls, display_name: str):
        super().__init__(chain_cls, display_name, [])

    def _increment(self, update, callback):
        message = get_message(update)
        Autobook.chat_autobook[message.chat_id][self.chain_cls.name].interval = \
            min(Autobook.chat_autobook[message.chat_id][self.chain_cls.name].interval + 1,
                Autobook.max_autobook_interval)
        self.display(message)

    def _decrement(self, update, callback):
        message = get_message(update)
        Autobook.chat_autobook[message.chat_id][self.chain_cls.name].interval = \
            max(Autobook.chat_autobook[message.chat_id][self.chain_cls.name].interval - 1,
                Autobook.min_autobook_interval)
        self.display(message)

    def display(self, message):
        m_down_interval = Menu(self.chain_cls, constants.M_DECREASE, [])
        m_interval_val = Menu(self.chain_cls,
                              str(Autobook.chat_autobook[message.chat_id][self.chain_cls.name].interval),
                              [])
        m_up_interval = Menu(self.chain_cls, constants.M_INCREASE, [])

        self.bot.updater.dispatcher.add_handler(CallbackQueryHandler(handle_exception(self._decrement),
                                                                     pattern=m_down_interval.name))
        self.bot.updater.dispatcher.add_handler(CallbackQueryHandler(handle_exception(self._increment),
                                                                     pattern=m_up_interval.name))

        message.edit_text(self.display_name, reply_markup=self._keyboard([m_down_interval, m_interval_val, m_up_interval]))

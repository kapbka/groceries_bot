# Menu classes

import uuid
import logging
from datetime import datetime
from telegram import ForceReply
from telegram.ext import CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from app.bot.telegram.helpers import get_message
from app.bot.telegram.creds import Creds
from app import constants
from app.waitrose import Waitrose


class Menu:
    def __init__(self, chain_name: str, display_name: str, children: list):
        self.chain_name = chain_name
        self.name = str(uuid.uuid4())
        self.display_name = display_name
        self.parent = None
        self.children = children
        self.bot = None

    def register(self, bot):
        self.bot = bot
        logging.debug(f'self.display_name {self.display_name}, {self.name}')
        wrapper = lambda u, c: self.display(get_message(u))
        bot.updater.dispatcher.add_handler(CallbackQueryHandler(wrapper, pattern=self.name))

        for c in self.children:
            c.parent = self
            c.register(bot)

    def display(self, message):
        logging.debug(f'self.display_name {self.display_name}, self.keyboard() {self._keyboard(self.children)}')
        message.edit_text(self.display_name, reply_markup=self._keyboard(self.children))

    def create(self, message):
        message.reply_text(self.display_name, reply_markup=self._keyboard(self.children))

    def _keyboard(self, children):
        disp_len = 0
        res = []
        sub_res = []
        for c in children:
            disp_len += len(c.display_name)
            btn = InlineKeyboardButton(c.display_name, callback_data=c.name)
            if disp_len > 33:
                res.append(sub_res)
                disp_len = len(c.display_name)
                sub_res = [btn]
            else:
                sub_res.append(btn)

        res.append(sub_res)

        if self.parent:
            res.append([InlineKeyboardButton('Back to ' + self.parent.display_name, callback_data=self.parent.name)])

        return InlineKeyboardMarkup(res)


class TextMenu(Menu):
    def __init__(self, chain_name: str, bot, display_name: str, text_message: str, next_menu: Menu = None):
        super().__init__(chain_name, display_name, [])
        self.text_message = text_message
        self.next_menu = next_menu
        if next_menu:
            next_menu.parent = self
        self.bot = bot

    def register(self, bot):
        logging.debug(f'TextMenu register {self.display_name}, {self.text_message}, {self.name}')

        if self.text_message not in bot.reply_menus:
            bot.reply_menus[self.text_message] = self.handle_response
            wrapper = lambda u, c: self.display(get_message(u))
            bot.updater.dispatcher.add_handler(CallbackQueryHandler(wrapper, pattern=self.name))
            if self.next_menu:
                self.next_menu.register(bot)

    def handle_response(self, message):
        pass

    def init_creds(self, message):
        if message.chat_id not in Creds.chat_creds or self.chain_name not in Creds.chat_creds[message.chat_id]:
            Creds.chat_creds[message.chat_id] = {self.chain_name: Creds(message.chat_id, self.chain_name)}


class LoginMenu(TextMenu):
    def display(self, message):
        self.init_creds(message)
        is_login_pwd = (Creds.chat_creds[message.chat_id][self.chain_name].login and
                        Creds.chat_creds[message.chat_id][self.chain_name].password)

        if not is_login_pwd or self.display_name == 'Login':
            msg = self.bot.bot.send_message(message.chat_id, self.text_message, reply_markup=ForceReply())
            message.delete()
        else:
            self.next_menu.display(message)

    def handle_response(self, message):
        Creds.chat_creds[message.chat_id][self.chain_name].login = message.text
        self.next_menu.display(message)


class PasswordMenu(TextMenu):
    def display(self, message):
        self.init_creds(message)
        is_login_pwd = (Creds.chat_creds[message.chat_id][self.chain_name].login and
                        Creds.chat_creds[message.chat_id][self.chain_name].password)

        if not is_login_pwd or self.parent.display_name == 'Login':
            msg = self.bot.bot.send_message(message.chat_id, self.text_message, reply_markup=ForceReply())
        else:
            self.next_menu.display(message)

    def handle_response(self, message):
        Creds.chat_creds[message.chat_id][self.chain_name].password = message.text

        if type(self.next_menu) == Menu:
            self.next_menu.create(message)
        else:
            self.next_menu.display(message)


class CvvMenu(TextMenu):
    def display(self, message):
        self.init_creds(message)
        is_cvv = Creds.chat_creds[message.chat_id][self.chain_name].cvv

        if not is_cvv or self.display_name == 'Payment':
            msg = self.bot.bot.send_message(message.chat_id, self.text_message, reply_markup=ForceReply())
            if type(self.parent) == Menu:
                message.delete()
        else:
            self.next_menu.display(message)

    def handle_response(self, message):
        Creds.chat_creds[message.chat_id][self.chain_name].cvv = message.text

        if type(self.next_menu) == Menu:
            self.next_menu.create(message)
        else:
            self.next_menu.display(message)


class SlotDayMenu(Menu):
    def __init__(self, chain_name: str, display_name: str):
        super().__init__(chain_name, display_name, [])

    def display(self, message):
        logging.debug(f'self.display_name {self.display_name}')

        # 1. getting slots
        chat_id = message.chat_id
        if self.chain_name == 'waitrose':
            chain = Waitrose(Creds.chat_creds[chat_id][self.chain_name].login,
                             Creds.chat_creds[chat_id][self.chain_name].password)
        else:
            raise ValueError(f'Unknown chain_name "{self.chain_name}"')
        all_slots = chain.get_all_available_slots()

        # 2. then we register children
        self.children.clear()
        slot_day = None
        for i, s in enumerate(all_slots.values()):
            if i == 0 or slot_day != datetime.strptime(s['startDateTime'], '%Y-%m-%dT%H:%M:%SZ').date():
                slot_day = datetime.strptime(s['startDateTime'], '%Y-%m-%dT%H:%M:%SZ').date()
                day_disp_name = f"{slot_day.day}-{slot_day.strftime('%B')[0:3]} " \
                            f"{str(constants.WEEKDAYS(slot_day.weekday()).name).capitalize()}"
                m_day = Menu(self.chain_name, day_disp_name, [])
                m_day.parent = self
                # append m_day as a child to Show available slots menu
                self.children.append(m_day)
                m_day.register(self.bot)

            # create slot menu
            slot_start_datetime = datetime.strptime(s['startDateTime'], '%Y-%m-%dT%H:%M:%SZ')
            slot_end_datetime = datetime.strptime(s['endDateTime'], '%Y-%m-%dT%H:%M:%SZ')
            slot_disp_name = "{:02d}:{:02d}-{:02d}:{:02d}".format(slot_start_datetime.hour, slot_start_datetime.minute,
                                                                  slot_end_datetime.hour, slot_end_datetime.minute)
            m_slot = SlotTimeMenu(self.chain_name, slot_disp_name, slot_start_datetime, slot_end_datetime)
            m_slot.parent = self.children[-1]
            # append m_slot as a child to m_day menu
            self.children[-1].children.append(m_slot)
            m_slot.register(self.bot)

        # 3. adding text
        message.edit_text(self.display_name, reply_markup=self._keyboard(self.children))


class SlotTimeMenu(Menu):
    def __init__(self, chain_name: str, display_name: str, start_datetime: datetime, end_datetime: datetime):
        super().__init__(chain_name, display_name, [])
        self.start_datetime = start_datetime
        self.end_datetime = end_datetime

    def display(self, message):
        logging.debug(f'self.display_name {self.display_name}')

        chat_id = message.chat_id
        if self.chain_name == 'waitrose':
            chain = Waitrose(Creds.chat_creds[chat_id][self.chain_name].login,
                             Creds.chat_creds[chat_id][self.chain_name].password)
        else:
            raise ValueError(f'Unknown chain_name "{self.chain_name}"')

        # slot booking
        chain.book_slot_default_address(self.start_datetime, self.end_datetime)


class FilterDayMenu(Menu):
    def __init__(self, chain_name: str, display_name: str):
        super().__init__(chain_name, display_name, [])

    def display(self, message):
        logging.debug(f'self.display_name {self.display_name}')

        self.children.clear()
        # 1. create filter day of week
        for wd in range(7):
            m_filter_day = Menu(self.chain_name, f'{str(constants.WEEKDAYS(wd).name).capitalize()}', [])
            m_filter_day.parent = self
            # append m_day as a child to Show available slots menu
            self.children.append(m_filter_day)
            m_filter_day.register(self.bot)

            # 2. create slots for the day of the week
            for st in range(7, 22):
                m_filter_slot = FilterTimeMenu(self.chain_name, f'{str(st)}:00-{str(st+1)}:00')
                m_filter_slot.parent = self.children[-1]
                # append m_slot as a child to m_day menu
                self.children[-1].children.append(m_filter_slot)
                m_filter_slot.register(self.bot)

        # 3. adding text
        message.edit_text(self.display_name, reply_markup=self._keyboard(self.children))


class FilterTimeMenu(Menu):
    def __init__(self, chain_name: str, display_name: str):
        super().__init__(chain_name, display_name, [])

    def display(self, message):
        logging.debug(f'self.display_name {self.display_name}')

        # TODO: write to a shared dict

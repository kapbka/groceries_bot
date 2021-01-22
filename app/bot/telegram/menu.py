# Menu classes

import uuid
from telegram import Update, Bot, ForceReply
from telegram.ext import CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from app.bot.telegram.helpers import get_message
from app.bot.telegram.creds import Creds
import logging


creds = {}


class Menu:
    def __init__(self, chain_name: str, display_name: str, children: list):
        self.chain_name = chain_name
        self.name = str(uuid.uuid4())
        self.display_name = display_name
        self.parent = None
        self.children = children

    def register(self, bot):
        logging.debug(f'self.display_name {self.display_name}, {self.name}')
        wrapper = lambda u, c: self.display(get_message(u))
        bot.updater.dispatcher.add_handler(CallbackQueryHandler(wrapper, pattern=self.name))

        for c in self.children:
            c.parent = self
            c.register(bot)

    def display(self, message):
        logging.debug(f'self.display_name {self.display_name}, self.keyboard() {self._keyboard()}')
        message.edit_text(self.display_name, reply_markup=self._keyboard())

    def create(self, message):
        message.reply_text(self.display_name, reply_markup=self._keyboard())

    def _keyboard(self):
        disp_len = 0
        res = []
        sub_res = []
        for c in self.children:
            disp_len += len(c.display_name)
            btn = InlineKeyboardButton(c.display_name, callback_data=c.name)
            if disp_len > 30:
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
        if message.chat_id not in creds or self.chain_name not in creds[message.chat_id]:
            creds[message.chat_id] = {self.chain_name: Creds(message.chat_id, self.chain_name)}


class LoginMenu(TextMenu):
    def display(self, message):
        self.init_creds(message)
        is_login_pwd = creds[message.chat_id][self.chain_name].login and creds[message.chat_id][self.chain_name].password

        if not is_login_pwd or self.display_name == 'Login':
            msg = self.bot.bot.send_message(message.chat_id, self.text_message, reply_markup=ForceReply())
            message.delete()
        else:
            self.next_menu.display(message)

    def handle_response(self, message):
        creds[message.chat_id][self.chain_name].login = message.text
        self.next_menu.display(message)


class PasswordMenu(TextMenu):
    def display(self, message):
        self.init_creds(message)
        is_login_pwd = creds[message.chat_id][self.chain_name].login and creds[message.chat_id][self.chain_name].password

        if not is_login_pwd or self.parent.display_name == 'Login':
            msg = self.bot.bot.send_message(message.chat_id, self.text_message, reply_markup=ForceReply())
        else:
            self.next_menu.display(message)

    def handle_response(self, message):
        creds[message.chat_id][self.chain_name].password = message.text

        if type(self.next_menu) == Menu:
            self.next_menu.create(message)
        else:
            self.next_menu.display(message)


class CvvMenu(TextMenu):
    def display(self, message):
        self.init_creds(message)
        is_cvv = creds[message.chat_id][self.chain_name].cvv

        if not is_cvv or self.display_name == 'Payment':
            msg = self.bot.bot.send_message(message.chat_id, self.text_message, reply_markup=ForceReply())
            if type(self.parent) == Menu:
                message.delete()
        else:
            self.next_menu.display(message)

    def handle_response(self, message):
        creds[message.chat_id][self.chain_name].cvv = message.text

        if type(self.next_menu) == Menu:
            self.next_menu.create(message)
        else:
            self.next_menu.display(message)

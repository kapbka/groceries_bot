# Text Menu classes

import logging
from telegram import ForceReply
from telegram.ext import CallbackQueryHandler
from app.bot.telegram.helpers import get_message
from app.bot.telegram.creds import Creds
from app.bot.telegram.chat_chain_cache import ChatChainCache
from app.bot.telegram.menu.menu import Menu
from app.bot.telegram import constants
from app.bot.log.exception_handler import handle_exception


class TextMenu(Menu):
    is_text_menu = True

    def __init__(self, chain_cls, bot, display_name: str, text_message: str, next_menu: Menu = None):
        super().__init__(chain_cls, display_name, [])
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
            bot.updater.dispatcher.add_handler(CallbackQueryHandler(handle_exception(wrapper), pattern=self.name))
            if self.next_menu:
                self.next_menu.register(bot)

    def handle_response(self, message):
        pass

    def init_creds(self, message):
        if message.chat_id not in Creds.chat_creds or self.chain_cls.name not in Creds.chat_creds[message.chat_id]:
            Creds.chat_creds[message.chat_id] = {self.chain_cls.name: Creds(message.chat_id, self.chain_cls.name)}


class LoginMenu(TextMenu):
    def display(self, message):
        self.init_creds(message)
        is_login_pwd = (Creds.chat_creds[message.chat_id][self.chain_cls.name].login and
                        Creds.chat_creds[message.chat_id][self.chain_cls.name].password)

        if not is_login_pwd or self.display_name == constants.M_LOGIN:
            msg = self.bot.bot.send_message(message.chat_id, self.text_message, reply_markup=ForceReply())
            message.delete()
        else:
            self.next_menu.display(message)

    def handle_response(self, message):
        Creds.chat_creds[message.chat_id][self.chain_cls.name].login = message.text
        self.next_menu.display(message)


class PasswordMenu(TextMenu):
    def display(self, message):
        self.init_creds(message)
        is_login_pwd = (Creds.chat_creds[message.chat_id][self.chain_cls.name].login and
                        Creds.chat_creds[message.chat_id][self.chain_cls.name].password)

        if not is_login_pwd or self.parent.display_name == constants.M_LOGIN:
            msg = self.bot.bot.send_message(message.chat_id, self.text_message, reply_markup=ForceReply())
        else:
            self.next_menu.display(message)

    def handle_response(self, message):
        Creds.chat_creds[message.chat_id][self.chain_cls.name].password = message.text

        ChatChainCache.invalidate(message.chat_id, self.chain_cls)

        if not self.next_menu.is_text_menu:
            self.next_menu.create(message)
        else:
            self.next_menu.display(message)


class CvvMenu(TextMenu):
    def display(self, message):
        self.init_creds(message)
        is_cvv = Creds.chat_creds[message.chat_id][self.chain_cls.name].cvv

        if not is_cvv or self.display_name == constants.M_CVV:
            msg = self.bot.bot.send_message(message.chat_id, self.text_message, reply_markup=ForceReply())
            if not self.parent.is_text_menu:
                message.delete()
        else:
            self.next_menu.display(message)

    def handle_response(self, message):
        Creds.chat_creds[message.chat_id][self.chain_cls.name].cvv = message.text

        if not self.next_menu.is_text_menu:
            self.next_menu.create(message)
        else:
            self.next_menu.display(message)

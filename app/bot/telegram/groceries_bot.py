# GroceriesBot class

import logging
import datetime
from telegram.ext import Updater
from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, Filters, CallbackContext
# bot
from app.bot.telegram.menu.menu import Menu, MainMenu, CheckoutMenu, SettingsMenu
from app.bot.telegram.menu.text_menu import LoginMenu, PasswordMenu, CvvMenu
from app.bot.telegram.menu.slot_menu import SlotsMenu
from app.bot.telegram.menu.filter_menu import FilterDaysMenu
from app.bot.telegram.helpers import get_message
from app.bot.telegram import constants
from app.db.api import connect
from collections import defaultdict
from app.bot.telegram.chat_menu_handlers import ChatMenuHandlers
from app.log.exception_handler import handle_exception


class GroceriesBot:
    def __init__(self, token: str, chains: list):
        if not chains:
            ValueError('Empty chain list!')

        self.chains = chains
        self.updater = Updater(token, use_context=True)
        self.bot = self.updater.bot
        self.reply_menus = defaultdict(lambda: defaultdict(defaultdict))
        self.root_menus = {}

        self.last_message = None

        # db connection
        connect()

    def create_menu(self, update: Update, context: CallbackContext):
        message = get_message(update)
        chat_id = message.chat_id

        if chat_id < 0:
            message.bot.send_message(chat_id=chat_id,
                                     text='Group chats are not supported yet.')
            return

        # text menus
        self.reply_menus.pop(chat_id, None)
        # clean registered menus
        ChatMenuHandlers.unregister_all_handlers(chat_id, self)
        #
        chain_login_menus = []
        chain_menus = []
        for chain_cls in self.chains:
            m_book_checkout_slots = SlotsMenu(chat_id, chain_cls, constants.M_AVAILABLE_SLOTS, make_checkout=True)
            m_book_slots = SlotsMenu(chat_id, chain_cls, constants.M_AVAILABLE_SLOTS)

            m_auto_booking = FilterDaysMenu(self, chat_id, chain_cls, constants.M_AUTOBOOKING)
            m_book_and_checkout = CvvMenu(chat_id, chain_cls, self, constants.M_BOOK_AND_CHECKOUT,
                                          f'{chain_cls.display_name}/{constants.M_BOOK_AND_CHECKOUT}: {constants.S_CVV}',
                                          m_book_checkout_slots)
            m_book = LoginMenu(chat_id, chain_cls, self, constants.M_BOOK, f'{chain_cls.display_name}/{constants.M_BOOK}: {constants.S_LOGIN}',
                               PasswordMenu(chat_id, chain_cls, self, constants.M_BOOK, f'{chain_cls.display_name}/{constants.M_BOOK}: {constants.S_PASSWORD}',
                                            m_book_slots))
            m_checkout = CvvMenu(chat_id, chain_cls, self, constants.M_CHECKOUT, f'{chain_cls.display_name}/{constants.M_CHECKOUT}: {constants.S_CVV}',
                                 CheckoutMenu(chat_id, chain_cls, constants.M_CHECKOUT, []))

            m_settings_password = PasswordMenu(chat_id, chain_cls, self, constants.M_PASSWORD, f'{chain_cls.display_name}/{constants.M_SETTINGS}: {constants.S_PASSWORD}', None)
            m_settings_login = LoginMenu(chat_id, chain_cls, self, constants.M_LOGIN, f'{chain_cls.display_name}/{constants.M_SETTINGS}: {constants.S_LOGIN}', m_settings_password)
            m_settings_payment = CvvMenu(chat_id, chain_cls, self, constants.M_CVV,
                                         f'{chain_cls.display_name}/{constants.M_SETTINGS}: {constants.S_CVV}', None)
            m_settings = SettingsMenu(chat_id, chain_cls, constants.M_SETTINGS, [m_settings_login, m_settings_payment])
            # update next menu once password or cvv entered
            m_settings_password.next_menu = m_settings
            m_settings_payment.next_menu = m_settings

            m_chain = MainMenu(chat_id, chain_cls, chain_cls.display_name, [m_auto_booking, m_book_and_checkout, m_book, m_checkout, m_settings])
            m_chain_login = LoginMenu(chat_id, chain_cls, self, chain_cls.display_name, f'{chain_cls.display_name}: {constants.S_LOGIN}',
                                      PasswordMenu(chat_id, chain_cls, self, chain_cls.display_name, f'{chain_cls.display_name}: {constants.S_PASSWORD}',
                                                   m_chain))
            m_book_checkout_slots.parent = m_chain_login
            m_book_slots.parent = m_chain_login

            chain_menus.append(m_chain)
            chain_login_menus.append(m_chain_login)

        self.root_menus[chat_id] = Menu(chat_id, None, constants.M_MAIN, chain_login_menus)
        self.root_menus[chat_id].register(self)
        for chain_menu in chain_menus:
            chain_menu.parent = self.root_menus[chat_id]

        return self.root_menus[chat_id].create(get_message(update))

    @staticmethod
    def help(update: Update, context: CallbackContext):
        message = get_message(update)

        message.bot.send_message(message.chat_id, constants.H_HELP)

    def run(self):
        self.updater.dispatcher.add_handler(CommandHandler('start', self.create_menu))
        self.updater.dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_exception(self.handle_text)))

        self.updater.dispatcher.add_handler(CommandHandler('help', self.help))

        self.updater.start_polling()

    def handle_text(self, update: Update, context: CallbackContext):
        message = get_message(update)

        if message.reply_to_message:
            # reply handler call
            self.reply_menus[message.chat_id][message.reply_to_message.text](message)

            # the previous invitation
            if message.reply_to_message.text:
                message.reply_to_message.delete()

            # the current user's input
            message.delete()

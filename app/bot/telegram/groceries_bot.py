# GroceriesBot class

import logging
import datetime
from telegram.ext import Updater
from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, Filters, CallbackContext
# bot
from app.bot.telegram.menu.menu import Menu, MainMenu, CheckoutMenu
from app.bot.telegram.menu.text_menu import LoginMenu, PasswordMenu, CvvMenu
from app.bot.telegram.menu.slot_menu import SlotsMenu
from app.bot.telegram.menu.filter_menu import FilterDayMenu
from app.bot.telegram.helpers import get_message


class GroceriesBot:
    def __init__(self, token: str, chains: list):
        if not chains:
            ValueError('Empty chain list!')

        self.chains = chains
        self.updater = Updater(token, use_context=True)
        self.bot = self.updater.bot
        self.reply_menus = {}

        self.last_message = None

    def create_menu(self, update: Update, context: CallbackContext):
        message = get_message(update)

        chain_login_menus = []
        chain_menus = []
        for chain_cls in self.chains:
            m_book_checkout_slots = SlotsMenu(chain_cls, 'All available slot days', make_checkout=True)
            m_book_slots = SlotsMenu(chain_cls, 'All available slot days')

            m_auto_booking = FilterDayMenu(chain_cls, 'Autobooking')
            m_book_slot_and_checkout = CvvMenu(chain_cls, self, 'Book slot and checkout',
                                               f'{chain_cls.display_name}/Book slot and checkout: Please enter your cvv',
                                               m_book_checkout_slots)
            m_book_slot = LoginMenu(chain_cls, self, 'Book slot', f'{chain_cls.display_name}/Book slot: Please enter your login',
                                    PasswordMenu(chain_cls, self, chain_cls.display_name, f'{chain_cls.display_name}/Book slot: Please enter your password',
                                                 m_book_slots))
            m_checkout = CvvMenu(chain_cls, self, 'Checkout', f'{chain_cls.display_name}/Checkout: Please enter your cvv',
                                 CheckoutMenu(chain_cls, 'Checkout', []))

            m_settings_password = PasswordMenu(chain_cls, self, 'Password', f'{chain_cls.display_name}/Settings: Please enter your password', None)
            m_settings_login = LoginMenu(chain_cls, self, 'Login', f'{chain_cls.display_name}/Settings: Please enter your login', m_settings_password)
            m_settings_payment = CvvMenu(chain_cls, self, 'Payment details',
                                         f'{chain_cls.display_name}/Settings: Please enter cvv of a payment card linked to your "{chain_cls.display_name}" profile', None)
            m_settings = Menu(chain_cls, 'Settings', [m_settings_login, m_settings_payment])
            # update next menu once password or cvv entered
            m_settings_password.next_menu = m_settings
            m_settings_payment.next_menu = m_settings

            m_chain = MainMenu(chain_cls, chain_cls.display_name, [m_auto_booking, m_book_slot_and_checkout, m_book_slot, m_checkout, m_settings])
            m_chain_login = LoginMenu(chain_cls, self, chain_cls.display_name, f'{chain_cls.display_name}: Please enter your login',
                                      PasswordMenu(chain_cls, self, chain_cls.display_name, f'{chain_cls.display_name}: Please enter your password',
                                                   m_chain))
            m_book_checkout_slots.parent = m_chain_login
            m_book_slots.parent = m_chain_login

            chain_menus.append(m_chain)
            chain_login_menus.append(m_chain_login)

        m_root = Menu(None, 'Main', chain_login_menus)
        m_root.register(self)
        for chain_menu in chain_menus:
            chain_menu.parent = m_root

        return m_root.create(get_message(update))

    def run(self):
        self.updater.dispatcher.add_handler(CommandHandler('start', self.create_menu))
        self.updater.dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, self.handle_text))
        self.updater.start_polling()

    def handle_text(self, update: Update, context: CallbackContext):
        message = get_message(update)

        # reply handler call
        self.reply_menus[message.reply_to_message.text](message)

        # the previous invitation
        if message.reply_to_message.text:
            message.reply_to_message.delete()

        # the current user's input
        message.delete()

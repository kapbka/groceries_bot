# GroceriesBot class

import logging
import datetime
from telegram.ext import Updater
from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, Filters, CallbackContext
# bot
from app.bot.telegram.menu.menu import Menu
from app.bot.telegram.menu.text_menu import LoginMenu, PasswordMenu, CvvMenu
from app.bot.telegram.menu.slot_menu import SlotDayMenu
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

        self.m_slots = {}
        self.m_settings = {}

        self.last_message = None

    def create_menu(self, update: Update, context: CallbackContext):
        message = get_message(update)

        chain_menus = []
        for chain_cls in self.chains:
            self.m_slots[chain_cls.name] = SlotDayMenu(chain_cls, 'All available slot days')

            m_auto_booking = FilterDayMenu(chain_cls, 'Autobooking')
            m_book_slot_and_checkout = LoginMenu(chain_cls, self, 'Book slot and checkout', f'{chain_cls.display_name}/Checkout: Please enter your login',
                                                 PasswordMenu(chain_cls, self, 'Password checkout', f'{chain_cls.display_name}/Checkout: Please enter your password',
                                                              CvvMenu(chain_cls, self, 'Cvv checkout', f'{chain_cls.display_name}/Checkout: Please enter your cvv', self.m_slots[chain_cls.name])))
            m_book_slot = LoginMenu(chain_cls, self, 'Book slot', f'{chain_cls.display_name}/Booking: Please enter your login',
                                    PasswordMenu(chain_cls, self, 'Password after booking', f'{chain_cls.display_name}/Booking: Please enter your password', self.m_slots[chain_cls.name]))
            m_checkout = CvvMenu(chain_cls, self, 'Checkout', f'{chain_cls.display_name}/Settings: Please enter your cvv', None)

            m_settings_password = PasswordMenu(chain_cls, self, 'Password', f'{chain_cls.display_name}/Settings: Please enter your password', None)
            m_settings_login = LoginMenu(chain_cls, self, 'Login', f'{chain_cls.display_name}/Settings: Please enter your login', m_settings_password)
            m_settings_payment = CvvMenu(chain_cls, self, 'Payment details', f'{chain_cls.display_name}/Settings: Please enter cvv of a payment card linked to your "{chain_cls.display_name}" profile', None)
            self.m_settings[chain_cls.name] = Menu(chain_cls, 'Settings', [m_settings_login, m_settings_payment])
            # update next menu once password or cvv entered
            m_settings_password.next_menu = self.m_settings[chain_cls.name]
            m_settings_payment.next_menu = self.m_settings[chain_cls.name]

            m_chain = Menu(chain_cls, chain_cls.display_name, [m_auto_booking, m_book_slot_and_checkout, self.m_settings[chain_cls.name]])
            self.m_slots[chain_cls.name].parent = m_chain

            chain_menus.append(m_chain)

        m_root = Menu(None, 'Main', chain_menus)
        m_root.register(self)

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

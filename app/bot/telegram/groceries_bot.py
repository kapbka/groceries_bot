# GroceriesBot class

from telegram.ext import Updater
from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, Filters, CallbackContext
from app.bot.telegram.menu import Menu, LoginMenu, PasswordMenu, CvvMenu, SlotDayMenu, FilterDayMenu
from app.bot.telegram.helpers import get_message
import logging


class GroceriesBot:
    def __init__(self, token: str, chains: list):
        if not chains:
            ValueError('Empty chain list!')

        self.chains = chains
        self.updater = Updater(token, use_context=True)
        self.bot = self.updater.bot
        self.reply_menus = {}

        self.m_root = None
        self.m_filter = {}
        self.m_settings = {}

        self.last_message = None

        self.create_menu()

    def create_menu(self):
        chain_menus = []
        for chain in self.chains:
            m_filter_slots = FilterDayMenu(chain, 'Filter slots')
            m_show_all_slots = SlotDayMenu(chain, 'All available slots')

            self.m_filter[chain] = Menu(chain, 'Filters', [m_filter_slots, m_show_all_slots])

            m_book_slot_and_checkout = LoginMenu(chain, self, 'Book slot and checkout', f'{chain.capitalize()}/Checkout: Please enter your login',
                                                 PasswordMenu(chain, self, 'Password checkout', f'{chain.capitalize()}/Checkout: Please enter your password',
                                                              CvvMenu(chain, self, 'Cvv checkout', f'{chain.capitalize()}/Checkout: Please enter your cvv', self.m_filter[chain])))
            m_book_slot = LoginMenu(chain, self, 'Book slot', f'{chain.capitalize()}/Booking: Please enter your login',
                                    PasswordMenu(chain, self, 'Password after booking', f'{chain.capitalize()}/Booking: Please enter your password', self.m_filter[chain]))

            m_settings_password = PasswordMenu(chain, self, 'Password', f'{chain.capitalize()}/Settings: Please enter your password', None)
            m_settings_login = LoginMenu(chain, self, 'Login', f'{chain.capitalize()}/Settings: Please enter your login', m_settings_password)
            m_settings_payment = CvvMenu(chain, self, 'Payment', f'{chain.capitalize()}/Settings: Please enter your cvv', None)
            self.m_settings[chain] = Menu(chain, 'Settings', [m_settings_login, m_settings_payment])
            # update next menu once password or cvv entered
            m_settings_password.next_menu = self.m_settings[chain]
            m_settings_payment.next_menu = self.m_settings[chain]

            m_chain = Menu(chain, chain.capitalize(), [m_book_slot_and_checkout, m_book_slot, self.m_settings[chain]])
            self.m_filter[chain].parent = m_chain

            chain_menus.append(m_chain)

        self.m_root = Menu(None, 'Main', chain_menus)
        self.updater.dispatcher.add_handler(CommandHandler('start', lambda u, c: self.m_root.create(get_message(u))))
        self.m_root.register(self)
        self.updater.dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, self.handle_text))

    def run(self):
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


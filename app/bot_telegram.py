# telegram bot classes

import uuid
from telegram.ext import Updater
from telegram import Update
from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import logging


class BotState:
    chain = None
    last_message = None
    state_list = []

    is_waiting_login = False
    is_waiting_password = False
    is_waiting_cvv = False

    @classmethod
    def change_state(cls, display_name):
        if display_name in cls.state_list:
            while cls.state_list[-1] != display_name:
                cls.state_list.pop()
        else:
            cls.state_list.append(display_name)

        logging.info(cls.state_list)


class Menu:
    def __init__(self, display_name: str, children: list):
        self.name = str(uuid.uuid4())
        self.display_name = display_name
        self.parent = None
        self.children = children

    def register(self, dispatcher):
        logging.debug( f'self.display_name {self.display_name}, {self.name}')
        dispatcher.add_handler(CallbackQueryHandler(self.display, pattern=self.name))
        for c in self.children:
            c.parent = self
            c.register(dispatcher)

    def display(self, bot, update):
        logging.debug(f'self.display_name {self.display_name}')
        logging.debug(f'self.keyboard() {self._keyboard()}')

        BotState.change_state(self.display_name)

        bot.callback_query.message.edit_text(self.display_name, reply_markup=self._keyboard())

    def create(self, bot, update, message=None):
        if not message:
            message = bot.message
        message.reply_text(self.display_name, reply_markup=self._keyboard())

    def _keyboard(self):
        res = [[InlineKeyboardButton(c.display_name, callback_data=c.name)] for c in self.children]
        if self.parent:
            res.append([InlineKeyboardButton('Back to ' + self.parent.display_name, callback_data=self.parent.name)])
        return InlineKeyboardMarkup(res)


class LoginMenu(Menu):
    def display(self, bot, update):
        BotState.change_state(self.display_name)
        BotState.last_message = bot.callback_query.message.reply_text('Please enter your login')
        bot.callback_query.message.delete()
        BotState.is_waiting_login = True


class Bot:
    def __init__(self, token: str, chains: list):
        if not chains:
            ValueError('Empty chain list!')

        self.chains = chains
        self.updater = Updater(token, use_context=True)

        self.m_root = None
        self.m_filter = {}

        self.last_message = None

        self.create_menu()

    def create_menu(self):
        chain_menus = []
        for chain in self.chains:
            m_filtered_slots = Menu('Filtered slots', [])
            m_all_available_slots = Menu('All available slots', [])

            m_filter_slots = Menu('Filter slots', [m_filtered_slots])
            m_show_all_available_slots = Menu('Show all available slots', [m_all_available_slots])

            self.m_filter[chain] = Menu('Filters', [m_filter_slots, m_show_all_available_slots])

            m_book_slot = LoginMenu('Book slot', [])
            m_book_slot_and_checkout = LoginMenu('Book slot and checkout', [])

            m_chain = Menu(chain.capitalize(), [m_book_slot, m_book_slot_and_checkout])
            self.m_filter[chain].parent = m_chain
            self.m_filter[chain].register(self.updater.dispatcher)

            chain_menus.append(m_chain)

        self.m_root = Menu('Main', chain_menus)
        self.updater.dispatcher.add_handler(CommandHandler('start', self.m_root.create))
        self.m_root.register(self.updater.dispatcher)
        self.updater.dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, self.handle_text))

    def run(self):
        self.updater.start_polling()

    def handle_text(self, update: Update, context: CallbackContext):
        # an invitation
        if BotState.last_message:
            BotState.last_message.delete()

        if BotState.is_waiting_login:
            BotState.last_message = update.message.reply_text('Please, enter password')
            BotState.is_waiting_login = False
            BotState.is_waiting_password = True
        elif BotState.is_waiting_password:
            BotState.last_message = update.message.reply_text('Please, enter cvv')
            BotState.is_waiting_password = False
            BotState.is_waiting_cvv = True
        elif BotState.is_waiting_cvv:
            BotState.is_waiting_cvv = False
            self.m_filter[BotState.state_list[0].lower()].create(None, None, update.message)
            BotState.change_state('Filters')

        # user's input
        update.message.delete()


if __name__ == '__main__':
    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)
    b = Bot('1579751582:AAEcot5v5NLyxXB1uFYQiBCyvBAsKOzGGsU', ['waitrose', 'tesco'])
    b.run()

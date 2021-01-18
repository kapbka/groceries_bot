# telegram bot classes

import uuid
from telegram.ext import Updater
from telegram import Update
from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from collections import defaultdict
import json
import logging


BOT_TOKEN = '1579751582:AAEcot5v5NLyxXB1uFYQiBCyvBAsKOzGGsU'
CHAIN_LIST = ['waitrose', 'tesco', 'sainsbury']


class BotState:
    chain = None
    last_message = None
    state_list = []

    is_waiting_login = False
    is_waiting_password = False
    is_waiting_cvv = False

    @staticmethod
    def get_creds(chat_id):
        with open('creds.json') as json_file:
            data = json.load(json_file)
        return data.get(str(chat_id), None)

    @staticmethod
    def update_creds(data):
        with open('creds.json', 'w') as outfile:
            json.dump(data, outfile)

    @classmethod
    def change_state(cls, display_name):
        if display_name in cls.state_list:
            while cls.state_list[-1] != display_name:
                cls.state_list.pop()
        else:
            cls.state_list.append(display_name)

        logging.debug(cls.state_list)


bot_state = defaultdict(BotState)


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

    def display(self, update, callback_context):
        logging.debug(f'self.display_name {self.display_name}')
        logging.debug(f'self.keyboard() {self._keyboard()}')

        bs = bot_state[update.callback_query.message.chat.id]
        bs.change_state(self.display_name)
        update.callback_query.message.edit_text(self.display_name, reply_markup=self._keyboard())

    def create(self, bot, update, message=None):
        if not message:
            message = bot.message
        bs = bot_state[message.chat.id]
        bs.change_state(self.display_name)
        message.reply_text(self.display_name, reply_markup=self._keyboard())

    def _keyboard(self):
        res = [[InlineKeyboardButton(c.display_name, callback_data=c.name)] for c in self.children]
        if self.parent:
            res.append([InlineKeyboardButton('Back to ' + self.parent.display_name, callback_data=self.parent.name)])
        return InlineKeyboardMarkup(res)


class LoginMenu(Menu):
    def __init__(self, display_name: str, children: list, filter_menu: Menu):
        super().__init__(display_name, children)
        self.filter_menu = filter_menu

    def display(self, bot, update):
        bs = bot_state[bot.callback_query.message.chat.id]

        creds = bs.get_creds(bot.callback_query.message.chat.id)

        bs.change_state(self.display_name)

        if not creds:
            bs.last_message = bot.callback_query.message.reply_text('Please enter your login')
            bot.callback_query.message.delete()
            bs.is_waiting_login = True
        else:
            self.filter_menu.display(bot, update)


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

            m_book_slot = LoginMenu('Book slot', [], self.m_filter[chain])
            m_book_slot_and_checkout = LoginMenu('Book slot and checkout', [], self.m_filter[chain])

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
        # if update.message.text.lower() == 'чмок':
        #     self.updater.bot.send_sticker(update.message.chat.id, 'CAADAgADZgkAAnlc4gmfCor5YbYYRAI')

        bs = bot_state[update.message.chat.id]

        creds = bs.get_creds(update.message.chat.id)

        # an invitation
        if bs.last_message:
            bs.last_message.delete()

        if not creds:
            if bs.is_waiting_login:
                bs.last_message = update.message.reply_text('Please, enter password')
                bs.is_waiting_login = False
                bs.is_waiting_password = True
            elif bs.is_waiting_password:
                bs.last_message = update.message.reply_text('Please, enter cvv')
                bs.is_waiting_password = False
                bs.is_waiting_cvv = True
            elif bs.is_waiting_cvv:
                bs.is_waiting_cvv = False
                self.m_filter[bs.state_list[1].lower()].create(None, None, update.message)
                bs.change_state('Filters')

            # user's input
            update.message.delete()
        else:
            self.m_filter[bs.state_list[1].lower()].create(None, None, update.message)
            bs.change_state('Filters')


if __name__ == '__main__':
    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)
    b = Bot(BOT_TOKEN, CHAIN_LIST)
    b.run()

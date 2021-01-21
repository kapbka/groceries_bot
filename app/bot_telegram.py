# telegram bot classes

import uuid
from telegram.ext import Updater
from telegram import Update, Bot, ForceReply
from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from collections import defaultdict
from enum import IntEnum
import json
import logging

BOT_TOKEN = '1579751582:AAEcot5v5NLyxXB1uFYQiBCyvBAsKOzGGsU'
CHAIN_LIST = ['waitrose'] # , 'tesco', 'coop', 'asda', 'lidl', 'sainsbury'


def get_message(update: Update):
    return update.message or update.callback_query.message


class CredMode(IntEnum):
    login = 0
    pwd = 1
    cvv = 2


class BotState:
    def __init__(self):
        self.chain_name = None
        self.last_message = None
        self.state_list = []

        self.login = None
        self.password = None
        self._cvv = None

    @property
    def cvv(self):
        return self._cvv

    @cvv.setter
    def cvv(self, value: int):
        if value and (not int(value) or len(str(value)) != 3):
            raise ValueError(f'Invalid cvv {value}, must be 3 digit number!')
        self._cvv = value

    def get_creds(self, chat_id: int):
        with open('creds.json') as json_file:
            data = json.load(json_file)
        return data.get(str(chat_id), {}).get(self.chain_name, {})

    def update_creds(self, chat_id: int, mode: int = CredMode.login):
        """
        User credentials update
        :param chat_id: chat id
        :param mode: CRED_MODE enum
        :return: writes to file and returns None
        """
        with open('creds.json') as json_file:
            data = json.load(json_file)

        if str(chat_id) not in data.keys():
            data[str(chat_id)] = {}
        if self.chain_name not in data[str(chat_id)].keys():
            data[str(chat_id)][self.chain_name] = {}

        if mode == CredMode.login:
            data[str(chat_id)][self.chain_name]['login'] = self.login
        elif mode == CredMode.pwd:
            data[str(chat_id)][self.chain_name]['password'] = self.password
        elif mode == CredMode.cvv:
            data[str(chat_id)][self.chain_name]['cvv'] = self.cvv

        with open('creds.json', 'w') as outfile:
            json.dump(data, outfile)

    def change_state(self, display_name: str):
        if display_name in self.state_list:
            while self.state_list[-1] != display_name:
                self.state_list.pop()
        else:
            self.state_list.append(display_name)

        if len(self.state_list) == 1:
            self.login = None
            self.password = None
            self.cvv = None
        elif len(self.state_list) == 2:
            self.chain_name = self.state_list[1].lower()

        logging.info(self.state_list)


bot_state = defaultdict(BotState)


class Menu:
    def __init__(self, display_name: str, children: list):
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
        logging.debug(f'self.display_name {self.display_name}')
        logging.debug(f'self.keyboard() {self._keyboard()}')

        bs = bot_state[message.chat.id]
        bs.change_state(self.display_name)
        message.edit_text(self.display_name, reply_markup=self._keyboard())

    def create(self, message):
        bs = bot_state[message.chat.id]
        bs.change_state(self.display_name)
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
    def __init__(self, bot, display_name: str, text_message: str, next_menu: Menu = None):
        super().__init__(display_name, [])
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

    def handle_response(self, message, bs: BotState):
        pass


class LoginMenu(TextMenu):
    def display(self, message):
        chat_id = message.chat.id
        bs = bot_state[chat_id]
        creds = bs.get_creds(chat_id)
        is_login_pwd = creds.get('login', None) and creds.get('password', None)
        bs.change_state(self.display_name)

        if not is_login_pwd or self.display_name == 'Login':
            bs.last_message = self.bot.bot.send_message(chat_id, self.text_message, reply_markup=ForceReply())
            message.delete()
        else:
            self.next_menu.display(message)

    def handle_response(self, message, bs: BotState):
        bs.login = message.text
        bs.update_creds(message.chat.id, CredMode.login)
        self.next_menu.display(message)


class PasswordMenu(TextMenu):
    def display(self, message):
        chat_id = message.chat.id
        bs = bot_state[chat_id]
        creds = bs.get_creds(chat_id)
        is_login_pwd = creds.get('login', None) and creds.get('password', None)
        bs.change_state(self.display_name)

        if not is_login_pwd or self.parent.display_name == 'Login':
            bs.last_message = self.bot.bot.send_message(chat_id, self.text_message, reply_markup=ForceReply())
        else:
            self.next_menu.display(message)

    def handle_response(self, message, bs: BotState):
        bs.password = message.text
        bs.update_creds(message.chat.id, CredMode.pwd)

        if type(self.next_menu) == Menu:
            self.next_menu.create(message)
        else:
            self.next_menu.display(message)


class CvvMenu(TextMenu):
    def display(self, message):
        chat_id = message.chat.id
        bs = bot_state[chat_id]
        creds = bs.get_creds(chat_id)
        is_cvv = creds.get('cvv')
        bs.change_state(self.display_name)

        if not is_cvv or self.display_name == 'Payment':
            bs.last_message = self.bot.bot.send_message(chat_id, self.text_message, reply_markup=ForceReply())
            if type(self.parent) == Menu:
                message.delete()
        else:
            self.next_menu.display(message)

    def handle_response(self, message, bs: BotState):
        bs.cvv = message.text
        bs.update_creds(message.chat.id, CredMode.cvv)

        if type(self.next_menu) == Menu:
            self.next_menu.create(message)
        else:
            self.next_menu.display(message)


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
            m_filtered_slots = Menu('Filtered slots', [])
            m_all_available_slots = Menu('All available slots', [])

            m_filter_slots = Menu('Filter slots', [m_filtered_slots])
            m_show_all_slots = Menu('Show all slots', [m_all_available_slots])

            self.m_filter[chain] = Menu('Filters', [m_filter_slots, m_show_all_slots])

            m_book_slot_and_checkout = LoginMenu(self, 'Book slot and checkout', 'Checkout: Please enter your login',
                                                 PasswordMenu(self, 'Password checkout', 'Checkout: Please enter your password',
                                                              CvvMenu(self, 'Cvv checkout', 'Checkout: Please enter your cvv', self.m_filter[chain])))
            m_book_slot = LoginMenu(self, 'Book slot', 'Booking: Please enter your login',
                                    PasswordMenu(self, 'Password after booking', 'Booking: Please enter your password', self.m_filter[chain]))

            m_settings_password = PasswordMenu(self, 'Password', 'Settings: Please enter your password', None)
            m_settings_login = LoginMenu(self, 'Login', 'Settings: Please enter your login', m_settings_password)
            m_settings_payment = CvvMenu(self, 'Payment', 'Settings: Please enter your cvv', None)
            self.m_settings[chain] = Menu('Settings', [m_settings_login, m_settings_payment])
            # update next menu once password or cvv entered
            m_settings_password.next_menu = self.m_settings[chain]
            m_settings_payment.next_menu = self.m_settings[chain]

            m_chain = Menu(chain.capitalize(), [m_book_slot_and_checkout, m_book_slot, self.m_settings[chain]])
            self.m_filter[chain].parent = m_chain

            chain_menus.append(m_chain)

        self.m_root = Menu('Main', chain_menus)
        self.updater.dispatcher.add_handler(CommandHandler('start', lambda u, c: self.m_root.create(get_message(u))))
        self.m_root.register(self)
        self.updater.dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, self.handle_text))

    def run(self):
        self.updater.start_polling()

    def handle_text(self, update: Update, context: CallbackContext):
        message = get_message(update)
        bs = bot_state[message.chat.id]

        # the previous invitation
        if bs.last_message:
            bs.last_message.delete()

        self.reply_menus[message.reply_to_message.text](message, bs)

        # user's input
        message.delete()


if __name__ == '__main__':
    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)
    b = GroceriesBot(BOT_TOKEN, CHAIN_LIST)
    b.run()

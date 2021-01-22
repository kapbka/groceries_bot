# telegram bot classes

import uuid
from telegram.ext import Updater
from telegram import Update, Bot, ForceReply
from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from collections import defaultdict
import json
import logging

BOT_TOKEN = '1579751582:AAEcot5v5NLyxXB1uFYQiBCyvBAsKOzGGsU'
CHAIN_LIST = ['waitrose', 'tesco'] # , 'coop', 'asda', 'lidl', 'sainsbury'


def get_message(update: Update):
    return update.message or update.callback_query.message


class Creds:
    def __init__(self, chat_id: int, chain_name: str):
        self.chat_id = chat_id
        self.chain_name = chain_name
        self.data = defaultdict(lambda: defaultdict(lambda: defaultdict(defaultdict)))

        with open('creds.json') as json_file:
            data = json.load(json_file)
            for chat_id, chat_data in data.items():
                for chain_name, creds in chat_data.items():
                    self.data[chat_id][chain_name].update(creds)

    def _save_creds(self):
        with open('creds.json', 'w') as outfile:
            json.dump(self.data, outfile, indent=2)

    @property
    def login(self):
        return self.data[str(self.chat_id)][self.chain_name]['login']

    @login.setter
    def login(self, value: str):
        self.data[str(self.chat_id)][self.chain_name]['login'] = value
        self._save_creds()

    @property
    def password(self):
        return self.data[str(self.chat_id)][self.chain_name]['password']

    @password.setter
    def password(self, value: str):
        self.data[str(self.chat_id)][self.chain_name]['password'] = value
        self._save_creds()

    @property
    def cvv(self):
        return self.data[str(self.chat_id)][self.chain_name]['cvv']

    @cvv.setter
    def cvv(self, value: str):
        if value and (not int(value) or len(value) != 3):
            raise ValueError(f'Invalid cvv {value}, must be 3 digit number!')

        self.data[str(self.chat_id)][self.chain_name]['cvv'] = int(value)
        self._save_creds()


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
            m_filtered_slots = Menu(chain, 'Filtered slots', [])
            m_all_available_slots = Menu(chain, 'All available slots', [])

            m_filter_slots = Menu(chain, 'Filter slots', [m_filtered_slots])
            m_show_all_slots = Menu(chain, 'Show all slots', [m_all_available_slots])

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

        # user's input
        message.delete()


if __name__ == '__main__':
    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)
    b = GroceriesBot(BOT_TOKEN, CHAIN_LIST)
    b.run()

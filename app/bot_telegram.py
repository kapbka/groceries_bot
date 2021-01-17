# telegram bot classes

import uuid
from telegram.ext import Updater
from telegram import Update
from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import logging


class BotState:
    is_waiting_login = False
    is_waiting_password = False
    is_waiting_cvv = False

    last_message = None

    state_list = []


class Menu:
    def __init__(self, display_name: str, children: list):
        self.name = str(uuid.uuid4())
        self.display_name = display_name
        self.parent = None
        self.children = children

    def register(self, dispatcher):
        logging.debug( f'REGISTER self.display_name {self.display_name}, {self.name}')
        dispatcher.add_handler(CallbackQueryHandler(self.display, pattern=self.name))
        for c in self.children:
            c.parent = self
            c.register(dispatcher)

    def display(self, bot, update):
        logging.debug(f'DISPLAY self.display_name {self.display_name}')
        logging.debug(f'DISPLAY self.keyboard() {self._keyboard()}')
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
        BotState.last_message = bot.callback_query.message.reply_text('Please enter your login')
        bot.callback_query.message.delete()
        BotState.is_waiting_login = True


class Bot:
    def __init__(self, token):
        self.updater = Updater(token, use_context=True)

        self.filter = Menu('Filters', [Menu('Filter slots', [
                                            Menu('Monday', [])]),
                                       Menu('Show all available slots', [
                                           Menu('Monday', [])])])

        m_book_slot = LoginMenu('Book slot', [])
        m_book_slot_and_checkout = LoginMenu('Book slot and checkout', [])

        m_waitrose = Menu('Waitrose', [m_book_slot, m_book_slot_and_checkout])
        m_tesco = Menu('Tesco', [])
        self.filter.parent = m_waitrose

        self.root_menu = Menu('Main', [m_waitrose, m_tesco])

        self.updater.dispatcher.add_handler(CommandHandler('start', self.root_menu.create))
        self.root_menu.register(self.updater.dispatcher)
        self.filter.register(self.updater.dispatcher)
        self.updater.dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, self.handle_text))

        self.last_message = None

    def run(self):
        self.updater.start_polling()

    def handle_text(self, update: Update, context: CallbackContext):
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
            self.filter.create(None, None, update.message)

        update.message.delete()


if __name__ == '__main__':
    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)
    b = Bot('1579751582:AAEcot5v5NLyxXB1uFYQiBCyvBAsKOzGGsU')
    b.run()

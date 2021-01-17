# telegram bot classes

import uuid
from telegram.ext import Updater
from telegram import Update
from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


class BotState:
    is_waiting_login = False
    is_waiting_password = False
    is_waiting_cvv = False


class Menu:
    def __init__(self, display_name: str, children: list):
        self.name = str(uuid.uuid4())
        self.display_name = display_name
        self.parent = None
        self.children = children

    def register(self, dispatcher):
        dispatcher.add_handler(CallbackQueryHandler(self.display, pattern=self.name))
        for c in self.children:
            c.parent = self
            c.register(dispatcher)

    def display(self, bot, update):
        bot.callback_query.message.edit_text(self.display_name, reply_markup=self.keyboard())

    def keyboard(self):
        res = [[InlineKeyboardButton(c.display_name, callback_data=c.name)] for c in self.children]
        if self.parent:
            res.append([InlineKeyboardButton('Back to ' + self.parent.display_name, callback_data=self.parent.name)])
        return InlineKeyboardMarkup(res)


class LoginMenu(Menu):
    def display(self, bot, update):
        bot.callback_query.message.reply_text('Please enter your login')
        BotState.is_waiting_login = True


class Bot:
    def __init__(self, token):
        self.updater = Updater(token, use_context=True)

        m_filtered_slots = Menu('Monday', [])
        m_all_available_slots = Menu('Monday', [])

        m_filter_slots = Menu('Filter slots', [m_filtered_slots])
        m_show_all_available = Menu('Show all available slots', [m_all_available_slots])

        self.filter = Menu('Filters', [m_filter_slots, m_show_all_available])

        m_login = LoginMenu('Login', [self.filter])

        m_book_slot = Menu('Book slot', [m_login])
        m_book_slot_and_checkout = Menu('Book slot and checkout', [m_login])
        self.filter.parent = m_book_slot

        m_waitrose = Menu('Waitrose', [m_book_slot, m_book_slot_and_checkout])
        m_tesco = Menu('Tesco', [])
        # m_filter_slots.parent = m_waitrose
        # m_show_all_available.parent = m_waitrose

        self.root_menu = Menu('Main', [m_waitrose, m_tesco])

        self.updater.dispatcher.add_handler(CommandHandler('start', self.start_menu))
        self.root_menu.register(self.updater.dispatcher)
        self.updater.dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, self.handle_text))

    def start_menu(self, bot, update):
        bot.message.reply_text(self.root_menu.display_name, reply_markup=self.root_menu.keyboard())

    def run(self):
        self.updater.start_polling()

    def handle_text(self, update: Update, context: CallbackContext):
        if BotState.is_waiting_login:
            update.message.reply_text('Please, enter password')
            BotState.is_waiting_login = False
            BotState.is_waiting_password = True
        elif BotState.is_waiting_password:
            update.message.reply_text('Please, enter cvv')
            BotState.is_waiting_password = False
            BotState.is_waiting_cvv = True
        elif BotState.is_waiting_cvv:
            BotState.is_waiting_cvv = False
            update.message.reply_text(self.filter.display_name, reply_markup=self.filter.keyboard())


if __name__ == '__main__':
    b = Bot('1579751582:AAEcot5v5NLyxXB1uFYQiBCyvBAsKOzGGsU')
    b.run()

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
        bot.callback_query.message.edit_text(self.display_name, reply_markup=self.menu_keyboard())

    def menu_keyboard(self):
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

        self.c3 = Menu('children3', [Menu('children4', [])])

        login = LoginMenu('Authentication', [])

        c11 = Menu('children11', [login])
        c12 = Menu('children12', [])
        self.c3.parent = c11

        c1 = Menu('children1', [c11, c12])
        c2 = Menu('children2', [])
        self.root_menu = Menu('root', [c1, c2])

        self.updater.dispatcher.add_handler(CommandHandler('start', self.start_menu))
        self.root_menu.register(self.updater.dispatcher)

        self.updater.dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, self.handle_text))

    def start_menu(self, bot, update):
        bot.message.reply_text(self.root_menu.display_name, reply_markup=self.root_menu.menu_keyboard())

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
            update.message.reply_text(self.c3.display_name, reply_markup=self.c3.menu_keyboard())


if __name__ == '__main__':
    b = Bot('1579751582:AAEcot5v5NLyxXB1uFYQiBCyvBAsKOzGGsU')
    b.run()

# telegram bot

from telegram.ext import Updater
from telegram.ext import CommandHandler, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


############################### Bot ############################################
def start(bot, update):
  bot.message.reply_text(main_menu_message(),
                         reply_markup=main_menu_keyboard())


def main_menu(bot, update):
  bot.callback_query.message.edit_text(main_menu_message(),
                          reply_markup=main_menu_keyboard())


def first_menu(bot, update):
  bot.callback_query.message.edit_text(first_menu_message(),
                          reply_markup=first_menu_keyboard())


def second_menu(bot, update):
  bot.callback_query.message.edit_text(second_menu_message(),
                          reply_markup=second_menu_keyboard())


def first_submenu(bot, update):
  pass

def second_submenu(bot, update):
  pass


def error(update, context):
    print(f'Update {update} caused error {context.error}')


############################ Keyboards #########################################
def main_menu_keyboard():
  keyboard = [[InlineKeyboardButton('Menu 1', callback_data='m1')],
              [InlineKeyboardButton('Menu 2', callback_data='m2')],
              [InlineKeyboardButton('Menu 3', callback_data='m3')]]
  return InlineKeyboardMarkup(keyboard)


def first_menu_keyboard():
  keyboard = [[InlineKeyboardButton('Submenu 1-1', callback_data='m1_1')],
              [InlineKeyboardButton('Submenu 1-2', callback_data='m1_2')],
              [InlineKeyboardButton('Main menu', callback_data='main')]]
  return InlineKeyboardMarkup(keyboard)


def second_menu_keyboard():
  keyboard = [[InlineKeyboardButton('Submenu 2-1', callback_data='m2_1')],
              [InlineKeyboardButton('Submenu 2-2', callback_data='m2_2')],
              [InlineKeyboardButton('Main menu', callback_data='main')]]
  return InlineKeyboardMarkup(keyboard)


############################# Messages #########################################
def main_menu_message():
  return 'Choose the option in main menu:'


def first_menu_message():
  return 'Choose the submenu in first menu:'


def second_menu_message():
  return 'Choose the submenu in second menu:'


############################# Handlers #########################################
updater = Updater('1579751582:AAEcot5v5NLyxXB1uFYQiBCyvBAsKOzGGsU', use_context=True)
updater.dispatcher.add_handler(CommandHandler('start', start))
updater.dispatcher.add_handler(CallbackQueryHandler(main_menu, pattern='main'))
updater.dispatcher.add_handler(CallbackQueryHandler(first_menu, pattern='m1'))
updater.dispatcher.add_handler(CallbackQueryHandler(second_menu, pattern='m2'))
updater.dispatcher.add_handler(CallbackQueryHandler(first_submenu, pattern='m1_1'))
updater.dispatcher.add_handler(CallbackQueryHandler(second_submenu, pattern='m2_1'))
updater.dispatcher.add_error_handler(error)

updater.start_polling()
################################################################################
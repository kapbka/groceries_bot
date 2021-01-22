# helpers
from telegram import Update


def get_message(update: Update):
    return update.message or update.callback_query.message
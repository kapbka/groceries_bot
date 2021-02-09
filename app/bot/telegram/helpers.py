# helpers
from telegram import Update
from app.bot.telegram.creds import Creds
from app.bot.telegram.chat_chain_cache import ChatChainCache


def get_message(update: Update):
    return update.message or update.callback_query.message


def get_chain_instance(chat_id, chain_cls):
    return ChatChainCache.create_or_get(chat_id, chain_cls,
                                        Creds.chat_creds[chat_id][chain_cls.name].login,
                                        Creds.chat_creds[chat_id][chain_cls.name].password)

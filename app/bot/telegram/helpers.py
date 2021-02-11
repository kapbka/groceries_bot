# helpers
from datetime import datetime, timedelta
from telegram import Update
from app.constants import WEEKDAYS
from app.bot.telegram.creds import Creds
from app.bot.telegram.chat_chain_cache import ChatChainCache


def get_message(update: Update):
    return update.message or update.callback_query.message


def get_chain_instance(chat_id, chain_cls):
    return ChatChainCache.create_or_get(chat_id, chain_cls,
                                        Creds.chat_creds[chat_id][chain_cls.name].login,
                                        Creds.chat_creds[chat_id][chain_cls.name].password)


def get_pretty_slot_name(slot_start_date: datetime, chain_cls):
    slot_end_date = slot_start_date + timedelta(hours=chain_cls.slot_interval_hrs)
    return f"{slot_start_date.day}-{slot_start_date.strftime('%B')[0:3]} " \
           f"{str(WEEKDAYS(slot_start_date.weekday()).name).capitalize()} " \
           f"{slot_start_date.strftime('%H:%M')}-{slot_end_date.strftime('%H:%M')}"

# helpers
from datetime import datetime, timedelta
from telegram import Update
from app.constants import WEEKDAYS
from app.bot.telegram.settings import Settings
from app.bot.telegram.chat_chain_cache import ChatChainCache


def get_message(update: Update):
    return update.message or update.callback_query.message


def get_chain_instance(chat_id, chain_cls):
    settings = Settings(chat_id, chain_cls.name)
    return ChatChainCache.create_or_get(chat_id, chain_cls, settings.login, settings.password)


def get_pretty_slot_day_name(slot_start_date: datetime):
    return f"{slot_start_date.day}-{slot_start_date.strftime('%B')[0:3]} " \
           f"{str(WEEKDAYS(slot_start_date.weekday()).name).capitalize()}"


def get_pretty_slot_time_name(ss_date: datetime, chain_cls):
    se_date = ss_date + timedelta(hours=chain_cls.slot_interval_hrs)
    return "{:02d}:{:02d}-{:02d}:{:02d}".format(ss_date.hour, ss_date.minute, se_date.hour, se_date.minute)


def get_pretty_slot_name(slot_start_date: datetime, chain_cls):
    return f"{get_pretty_slot_day_name(slot_start_date)} {get_pretty_slot_time_name(slot_start_date, chain_cls)}"


def get_pretty_filter_slot_time_name(start_hour, chain_cls):
    return "{:02d}:00-{:02d}:00".format(start_hour, start_hour + chain_cls.slot_interval_hrs)

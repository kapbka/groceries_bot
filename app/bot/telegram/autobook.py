# Filter class to store filters setting per chat/chain

import json
import logging
from telegram.ext import Updater
from collections import defaultdict
from datetime import datetime, timedelta
from app.constants import WEEKDAYS
from app.bot.telegram import constants
from app.bot.telegram.settings import Settings
from app.bot.telegram.helpers import get_chain_instance, get_pretty_slot_name
from app.db.models import Chain
from app.tesco.tesco import Tesco
from app.waitrose.waitrose import Waitrose
from app.db.api import connect


class Autobook(object):
    BOT_TOKEN = '1579751582:AAEcot5v5NLyxXB1uFYQiBCyvBAsKOzGGsU'
    BOT = Updater(BOT_TOKEN, use_context=True).bot

    @staticmethod
    def _get_first_matching_slot(chain, filters: dict, interval: int):
        slots = chain.get_slots()

        # no slots
        if not slots:
            return None

        # if filters are not populated then we return the first available slot
        if not filters:
            return slots[0]

        # if filters are populated, we get the first matching slot
        slot_days = sorted(set(s.date() for s in slots))
        for sd in slot_days:
            wd = WEEKDAYS(sd.weekday()).name[0:3]
            last_order_date = chain.get_last_order_date()
            if wd not in filters or (last_order_date and last_order_date + timedelta(days=interval) > sd):
                continue
            # if week day matches then go through slot times
            slot_times = list(filter(lambda x: x.date() == sd, slots))
            for st in slot_times:
                # if time matches then book and checkout
                if st.time().hour in filters[wd]:
                    logging.info(f'{constants.S_SLOT_FOUND}: {st}')
                    return st

        # no matching slots according to the filters
        logging.debug(constants.S_NO_MATCHING_SLOT)
        return None

    def do_autobook(self):
        data = list(Chain.objects())
        for chat_chain in data:
            if not chat_chain.autobook.enabled:
                continue
            chain_cls = eval(chat_chain.name.capitalize())
            chain = get_chain_instance(chat_chain.chat_id, chain_cls)
            slot = self._get_first_matching_slot(chain, chat_chain.autobook.filters, chat_chain.autobook.interval)
            if slot:
                chain.book(slot)
                res = chain.checkout(Settings(chat_chain.chat_id, chat_chain.name).cvv)
                conf_msg = f'{chat_chain.name.capitalize()}: slot "{get_pretty_slot_name(slot, chain_cls)}" ' \
                           f'has been {constants.S_BOOKED} and {constants.S_CHECKED_OUT}. ' \
                           f'{constants.S_ORDER_NUMBER} "{res}".'
                logging.info(f'chat_id={chat_chain.chat_id}, chain={chat_chain.name}: {conf_msg}')
                Autobook.BOT.send_message(chat_chain.chat_id, conf_msg)
            else:
                logging.info(f'No suitable slot to book for chat_id={chat_chain.chat_id}, chain={chat_chain.name}')


if __name__ == '__main__':
    connect()
    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
    a = Autobook()
    a.do_autobook()

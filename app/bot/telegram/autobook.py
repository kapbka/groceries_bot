# Filter class to store filters setting per chat/chain

import json
import logging
from telegram.ext import Updater
from collections import defaultdict
from datetime import datetime, timedelta
from app.constants import WEEKDAYS
from app.bot.telegram import constants
from app.bot.telegram.creds import Creds
from app.bot.telegram.helpers import get_chain_instance, get_pretty_slot_name
from app.tesco.tesco import Tesco
from app.waitrose.waitrose import Waitrose


BOT_TOKEN = '1579751582:AAEcot5v5NLyxXB1uFYQiBCyvBAsKOzGGsU'


class Autobook(object):
    chat_autobook = {}
    default_autobook_interval = 7
    max_autobook_interval = 14
    min_autobook_interval = 1

    bot = Updater(BOT_TOKEN, use_context=True).bot

    def __init__(self, chat_id: int, chain_name: str):
        self.chat_id = chat_id
        self.chain_name = chain_name
        self.data = defaultdict(lambda: defaultdict(lambda: defaultdict(defaultdict)))

        with open('settings_data/autobook.json') as json_file:
            data = json.load(json_file)
            for chat_id, chat_data in data.items():
                for chain_name, autobook_data in chat_data.items():
                    for key, value in autobook_data.items():
                        if isinstance(value, dict):
                            self.data[chat_id][chain_name][key].update(value)
                        else:
                            self.data[chat_id][chain_name][key] = value

    def __getattr__(self, item):
        if item in ['chat_id', 'chat_name', 'data']:
            return object.__getattribute__(self, item)
        elif item == 'autobook':
            return self.data[str(self.chat_id)][self.chain_name].get(item, False)
        elif item == 'interval':
            return self.data[str(self.chat_id)][self.chain_name].get(item, Autobook.default_autobook_interval)
        else:
            return self.data[str(self.chat_id)][self.chain_name]['filters'].get(item, [])

    def __setattr__(self, key, value):
        if key in ['chat_id', 'chain_name', 'data']:
            super().__setattr__(key, value)
        else:
            if key in ('autobook', 'interval'):
                self.data[str(self.chat_id)][self.chain_name][key] = value
            else:
                if value:
                    self.data[str(self.chat_id)][self.chain_name]['filters'][key] = value
                else:
                    del self.data[str(self.chat_id)][self.chain_name]['filters'][key]

            # save filters to file
            with open('settings_data/autobook.json', 'w') as outfile:
                json.dump(self.data, outfile, indent=2)

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
        for chat_id, chat_data in self.data.items():
            for chain_name, chain_data in chat_data.items():
                if not chain_data['autobook']:
                    continue
                chain_cls = eval(chain_name.capitalize())
                chain = get_chain_instance(chat_id, chain_cls)
                interval = chain_data.get('interval', Autobook.default_autobook_interval)
                slot = self._get_first_matching_slot(chain, chain_data['filters'], interval)
                if slot:
                    chain.book(slot)
                    res = chain.checkout(Creds.chat_creds[chat_id][chain_name].cvv)
                    conf_msg = f'{chain_name.capitalize()}: slot "{get_pretty_slot_name(slot, chain_cls)}" ' \
                               f'has been {constants.S_BOOKED} and {constants.S_CHECKED_OUT}. ' \
                               f'{constants.S_ORDER_NUMBER} "{res}".'
                    logging.info(f'chat_id={chat_id}, chain={chain_name}: {conf_msg}')
                    Autobook.bot.send_message(chat_id, conf_msg)
                else:
                    logging.info(f'No suitable slot to book for chat_id={chat_id}, chain={chain_name}')


if __name__ == '__main__':
    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
    Creds.chat_creds['365436333'] = {"tesco": Creds("365436333", 'tesco'), "waitrose": Creds("365436333", 'waitrose')}
    a = Autobook('365436333', 'tesco')
    a.do_autobook()

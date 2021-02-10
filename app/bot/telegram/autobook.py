# Filter class to store filters setting per chat/chain

from collections import defaultdict
from datetime import datetime
import json
import logging
from app.constants import WEEKDAYS
from app.bot.telegram.creds import Creds
from app.bot.telegram.helpers import get_chain_instance
from app.tesco.tesco import Tesco


class Autobook(object):
    chat_autobook = {}
    default_autobook_interval = 7
    max_autobook_interval = 14
    min_autobook_interval = 1

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
    def _get_first_matching_slot(chain, filters):
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
            if wd not in filters:
                continue
            # if week day matches then go through slot times
            slot_times = list(filter(lambda x: x.date() == sd, slots))
            for st in slot_times:
                # if time matches then book and checkout
                if st.time().hour in filters[wd]:
                    logging.info(f'Matching slot found {st}')
                    return st

        # no matching slots according to the filters
        logging.debug(f'No matching slot found!')
        return None

    def do_autobook(self):
        for chat_id, chat_data in self.data.items():
            for chain_name, chain_data in chat_data.items():
                if not chain_data['autobook']:
                    continue
                chain = get_chain_instance(chat_id, eval(chain_name.capitalize()))
                slot = self._get_first_matching_slot(chain, chain_data['filters'])
                if slot:
                    chain.book(slot)
                    logging.debug(f'chat_id={chat_id}, chain={chain_name}, slot={slot} has been booked')
                    res = None # chain.checkout(Creds.chat_creds[chat_id][chain_name].cvv)
                    logging.info(f'chat_id={chat_id}, chain={chain_name}, '
                                 f'slot {slot} has been checked out. Order number is {res}')
                else:
                    logging.info(f'No suitable slot to book for chat_id={chat_id}, chain={chain_name}')


if __name__ == '__main__':
    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)
    Creds.chat_creds['365436333'] = {"tesco": Creds("365436333", 'tesco')}
    a = Autobook('365436333', 'tesco')
    a.do_autobook()

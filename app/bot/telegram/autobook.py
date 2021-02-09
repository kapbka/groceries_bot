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
        else:
            return self.data[str(self.chat_id)][self.chain_name]['filters'].get(item, [])

    def __setattr__(self, key, value):
        if key in ['chat_id', 'chain_name', 'data']:
            super().__setattr__(key, value)
        else:
            if key == 'autobook':
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
    def _get_first_matching_slot(slots, filters):
        for sd in set(s.date() for s in slots):
            wd = WEEKDAYS(sd.weekday()).name[0:3]
            if wd in filters:
                # if week day matches then go through slot times
                for sdt in filter(lambda x: x.date() == sd, slots):
                    # if time matches then book and checkout
                    if sdt.time().hour in filters[wd]:
                        logging.debug(f'Matching slot found {sdt}')
                        return sdt
        logging.debug(f'No matching slot found!')
        return None

    def autobook(self):
        # go through chats
        for chat_id, chat_data in self.data.items():
            # go through chains
            for chain_name, chain_data in chat_data.items():
                # if autobook option is on
                if chain_data['autobook']:
                    chain = get_chain_instance(chat_id, Tesco)
                    slots = chain.get_slots()
                    if slots:
                        # if filters are populated, we get the first matching slot
                        if chain_data['filters']:
                            slot = self._get_first_matching_slot(slots, chain_data['filters'])
                        # if filters are not populated then we book the first available slot
                        else:
                            slot = slots[0]

                        if slot:
                            chain.book(slot)
                            logging.debug(f'chat_id={chat_id}, chain={chain_name}, slot={slot} has been booked')
                            # res = chain.checkout(Creds.chat_creds[chat_id][chain_name].cvv)
                            # logging.debug(f'chat_id={chat_id}, chain={chain_name},
                            # slot {slot} has been checked out. Order number is {res}')
                        else:
                            logging.debug(f'No slots to book chat_id={chat_id}, chain={chain_name}')


if __name__ == '__main__':
    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
    Creds.chat_creds['365436333'] = {"tesco": Creds("365436333", 'tesco')}
    a = Autobook('365436333', 'tesco')
    a.autobook()

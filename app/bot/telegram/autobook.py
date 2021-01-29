# Filter class to store filters setting per chat/chain

from collections import defaultdict
from datetime import datetime
import json
import logging


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
                self.data[str(self.chat_id)][self.chain_name]['filters'][key] = value

            # save filters to file
            with open('settings_data/autobook.json', 'w') as outfile:
                json.dump(self.data, outfile, indent=2)

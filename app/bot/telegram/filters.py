# Filter class to store filters setting per chat/chain

from collections import defaultdict
from datetime import datetime
import json
import logging


class Filter(object):
    chat_filters = {}

    def __init__(self, chat_id: int, chain_name: str):
        self.chat_id = chat_id
        self.chain_name = chain_name
        self.data = defaultdict(lambda: defaultdict(lambda: defaultdict()))

        with open('settings_data/filters.json') as json_file:
            data = json.load(json_file)
            for chat_id, chat_data in data.items():
                for chain_name, filters in chat_data.items():
                    self.data[chat_id][chain_name].update(filters)

    def __getattr__(self, item):
        if item in ['chat_id', 'chat_name', 'data']:
            return object.__getattribute__(self, item)
        else:
            return self.data[str(self.chat_id)][self.chain_name].get(item, [])

    def __setattr__(self, key, value):
        if key in ['chat_id', 'chain_name', 'data']:
            super().__setattr__(key, value)
        else:
            # validate value
            # if datetime.strptime(value, '%H:%M').time():
            #     raise ValueError(f'Invalid time!')

            # set property
            self.data[str(self.chat_id)][self.chain_name][key] = value

            # save filters to file
            with open('settings_data/filters.json', 'w') as outfile:
                json.dump(self.data, outfile, indent=2)

    def __delattr__(self, item, value):
        self.data[str(self.chat_id)][self.chain_name][item].remove(value)

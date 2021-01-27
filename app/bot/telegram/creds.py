# Creds class

from collections import defaultdict
import json
import logging


class Creds:
    chat_creds = {}

    def __init__(self, chat_id: int, chain_name: str):
        self.chat_id = chat_id
        self.chain_name = chain_name
        self.data = defaultdict(lambda: defaultdict(lambda: defaultdict(defaultdict)))

        with open('settings_data/creds.json') as json_file:
            data = json.load(json_file)
            for chat_id, chat_data in data.items():
                for chain_name, creds in chat_data.items():
                    self.data[chat_id][chain_name].update(creds)

    def _save_creds(self):
        with open('settings_data/creds.json', 'w') as outfile:
            json.dump(self.data, outfile, indent=2)

    @property
    def login(self):
        return self.data[str(self.chat_id)][self.chain_name]['login']

    @login.setter
    def login(self, value: str):
        self.data[str(self.chat_id)][self.chain_name]['login'] = value
        self._save_creds()

    @property
    def password(self):
        return self.data[str(self.chat_id)][self.chain_name]['password']

    @password.setter
    def password(self, value: str):
        self.data[str(self.chat_id)][self.chain_name]['password'] = value
        self._save_creds()

    @property
    def cvv(self):
        return self.data[str(self.chat_id)][self.chain_name]['cvv']

    @cvv.setter
    def cvv(self, value: str):
        if value and (not int(value) or len(value) != 3):
            raise ValueError(f'Invalid cvv {value}, must be 3 digit number!')

        self.data[str(self.chat_id)][self.chain_name]['cvv'] = int(value)
        self._save_creds()

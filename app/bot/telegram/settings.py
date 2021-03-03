# Settings class

from app.db.models import Chain
from app.db.api import encrypt, decrypt


class Settings(object):
    max_autobook_interval = 14
    min_autobook_interval = 1
    default_autobook_interval = 7

    def __init__(self, chat_id: int, chain_name: str):
        obj = Chain.objects(chat_id=chat_id, name=chain_name)
        if len(obj) > 0:
            self.db_obj = obj[0]
        else:
            self.db_obj = Chain(chat_id=chat_id, name=chain_name)
        self.chat_id = chat_id
        self.chain_name = chain_name

    def __getattr__(self, item):
        if item in ['db_obj', 'chat_id', 'chain_name']:
            return object.__getattribute__(self, item)
        elif item == 'login':
            return self.db_obj.creds.login
        elif item == 'password':
            pwd = self.db_obj.creds.password
            if pwd:
                return decrypt(pwd, str(self.chat_id) + self.chain_name)
            else:
                return None
        elif item == 'cvv':
            return self.db_obj.creds.cvv
        elif item == 'ab_enabled':
            return self.db_obj.autobook.enabled
        elif item == 'ab_interval':
            return self.db_obj.autobook.interval or Settings.default_autobook_interval
        # days of the week
        else:
            return self.db_obj.autobook.filters.get(item, [])

    def __setattr__(self, key, value):
        if key in ['db_obj', 'chat_id', 'chain_name']:
            super().__setattr__(key, value)
        else:
            if key == 'login':
                self.db_obj.creds.login = value
            elif key == 'password':
                self.db_obj.creds.password = encrypt(value, str(self.chat_id) + self.chain_name)
            elif key == 'cvv':
                if value and (not int(value) or len(value) != 3):
                    raise ValueError(f'Invalid cvv {value}, must be 3 digit number!')
                self.db_obj.creds.cvv = int(value)
            elif key == 'ab_enabled':
                self.db_obj.autobook.enabled = value
            elif key == 'ab_interval':
                self.db_obj.autobook.interval = value
            # day of the week
            else:
                if value:
                    self.db_obj.autobook.filters[key] = value
                else:
                    del self.db_obj.autobook.filters[key]

            self.db_obj.save()

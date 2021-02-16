# chat and chain specific cache class

import logging
from datetime import datetime, timedelta
from collections import defaultdict


class ChatChainCache:
    instance_cache = defaultdict(lambda: defaultdict(lambda: defaultdict(defaultdict)))

    @staticmethod
    def create_or_get(chat_id, chain_cls, login, password):
        data = ChatChainCache.instance_cache[chat_id][chain_cls.name]

        if (not data['last_access_date'] or data['last_access_date'] +
            timedelta(seconds=chain_cls.session_expiry_sec) < datetime.now()
           ):
            logging.debug(f'Cache creation {chain_cls.name}')
            data['instance'] = chain_cls(login, password)

        data['last_access_date'] = datetime.now()

        return data['instance']

    @staticmethod
    def invalidate(chat_id, chain_cls):
        logging.debug(f'Cache invalidation {chain_cls.name}')

        ChatChainCache.instance_cache[chat_id][chain_cls.name]['last_access_date'] = \
            datetime.now() - timedelta(seconds=(chain_cls.session_expiry_sec + 1))

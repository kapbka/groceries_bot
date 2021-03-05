# chat menus, mainly to unregister

import logging
from collections import defaultdict


class ChatMenuHandlers:
    handlers = defaultdict(list)

    @staticmethod
    def add_handler(bot, chat_id, handler):
        logging.debug(f'Adding handler {handler}')
        bot.updater.dispatcher.add_handler(handler)
        ChatMenuHandlers.handlers[chat_id].append(handler)

    @staticmethod
    def unregister_all_handlers(chat_id, bot):
        for handler in ChatMenuHandlers.handlers[chat_id]:
            logging.debug(f'Removing handler {handler}')
            bot.updater.dispatcher.remove_handler(handler)
        ChatMenuHandlers.handlers.pop(chat_id, None)

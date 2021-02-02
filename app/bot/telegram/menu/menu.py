# Menu classes

import uuid
import logging
from telegram.ext import CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from app.bot.telegram.helpers import get_message


class Menu:
    def __init__(self, chain_cls, display_name: str, children: list, alignment_len: int = 22):
        self.chain_cls = chain_cls
        self.name = str(uuid.uuid4())
        self.display_name = display_name
        self.parent = None
        self.children = children
        self.bot = None
        self.alignment_len = alignment_len

    def register(self, bot):
        self.bot = bot
        logging.debug(f'self.display_name {self.display_name}, {self.name}')
        wrapper = lambda u, c: self.display(get_message(u))
        bot.updater.dispatcher.add_handler(CallbackQueryHandler(wrapper, pattern=self.name))

        for c in self.children:
            c.parent = self
            c.register(bot)

    def display(self, message):
        logging.debug(f'self.display_name {self.display_name}, self.keyboard() {self._keyboard(self.children)}')
        message.edit_text(self.display_name, reply_markup=self._keyboard(self.children))

    def create(self, message):
        message.reply_text(self.display_name, reply_markup=self._keyboard(self.children))

    def _keyboard(self, children):
        disp_len = 0
        res = []
        sub_res = []
        for c in children:
            disp_len += len(c.display_name)
            btn = InlineKeyboardButton(c.display_name, callback_data=c.name)
            if disp_len > c.alignment_len:
                res.append(sub_res)
                disp_len = len(c.display_name)
                sub_res = [btn]
            else:
                sub_res.append(btn)

        res.append(sub_res)

        if self.parent:
            res.append([InlineKeyboardButton('Back to ' + self.parent.display_name, callback_data=self.parent.name)])

        return InlineKeyboardMarkup(res)

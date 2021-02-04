# Menu classes

import uuid
import logging
from datetime import datetime, timedelta
from telegram.ext import CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from app.constants import WEEKDAYS
from app.bot.telegram.helpers import get_message
from app.bot.telegram.chat_chain_cache import ChatChainCache
from app.bot.telegram.creds import Creds


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


class CheckoutMenu(Menu):
    def register(self, bot):
        self.parent = self.parent.parent
        super().register(bot)

    def display(self, message):
        logging.debug(f'self.display_name {self.display_name}, self.keyboard() {self._keyboard(self.children)}')

        chain = ChatChainCache.create_or_get(message.chat_id, self.chain_cls,
                                             Creds.chat_creds[message.chat_id][self.chain_cls.name].login,
                                             Creds.chat_creds[message.chat_id][self.chain_cls.name].password)

        cur_slot = chain.get_current_slot()
        cur_slot_end = cur_slot + timedelta(hours=chain.slot_interval_hrs)

        if not cur_slot:
            raise ValueError('The booked slot has expired, please book a new slot')

        slot_disp_name = f"{cur_slot.day}-{cur_slot.strftime('%B')[0:3]} " \
                          f"{str(WEEKDAYS(cur_slot.weekday()).name).capitalize()} " \
                          f"{cur_slot.strftime('%H:%M')}-{cur_slot_end.strftime('%H:%M')}"

        m_slot = CheckoutSlotMenu(self.chain_cls, slot_disp_name, [])
        m_slot.register(self.bot)
        m_slot.parent = self.parent

        message.edit_text(self.display_name, reply_markup=self._keyboard([m_slot]))


class CheckoutSlotMenu(Menu):
    def display(self, message):
        logging.debug(f'self.display_name {self.display_name}, self.keyboard() {self._keyboard(self.children)}')

        chain = ChatChainCache.create_or_get(message.chat_id, self.chain_cls,
                                             Creds.chat_creds[message.chat_id][self.chain_cls.name].login,
                                             Creds.chat_creds[message.chat_id][self.chain_cls.name].password)

        cur_slot = chain.get_current_slot()
        cur_slot_end = cur_slot + timedelta(hours=chain.slot_interval_hrs)

        if not cur_slot:
            raise ValueError('The booked slot has expired, please book a new slot')

        res = chain.checkout(Creds.chat_creds[message.chat_id][self.chain_cls.name].cvv)

        disp_name = f"Slot {cur_slot.day}-{cur_slot.strftime('%B')[0:3]} " \
                    f"{str(WEEKDAYS(cur_slot.weekday()).name).capitalize()} " \
                    f"{cur_slot.strftime('%H:%M')}-{cur_slot_end.strftime('%H:%M')} is checked out. " \
                    f"Order number is {res}"

        message.edit_text(disp_name, reply_markup=self._keyboard([]))


class MainMenu(Menu):
    def display(self, message):
        logging.debug(f'self.display_name {self.display_name}, self.keyboard() {self._keyboard(self.children)}')
        logging.info(f'Loggining into "{self.display_name.capitalize()} account"')

        chain = ChatChainCache.create_or_get(message.chat_id, self.chain_cls,
                                             Creds.chat_creds[message.chat_id][self.chain_cls.name].login,
                                             Creds.chat_creds[message.chat_id][self.chain_cls.name].password)

        new_children = []
        for c in self.children:
            # TODO: replace with a class name
            if c.display_name != 'Checkout' or chain.get_current_slot():
                new_children.append(c)

        message.edit_text(self.display_name, reply_markup=self._keyboard(new_children))

# Menu classes

import uuid
import logging
from telegram.ext import CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from app.bot.telegram.helpers import get_message, get_chain_instance, get_pretty_slot_name, asynchronous
from app.bot.telegram.settings import Settings
from app.bot.telegram import constants
from app.log.exception_handler import handle_exception
from app.log.status_bar import ProgressBarWriter
from app.bot.telegram.chat_menu_handlers import ChatMenuHandlers
import app.bot.telegram.constants


class Menu:
    is_text_menu = False

    def __init__(self, chat_id, chain_cls, display_name: str, children: list, alignment_len: int = 22):
        self.chat_id = chat_id
        self.chain_cls = chain_cls
        self.name = str(uuid.uuid4())
        self.display_name = display_name
        self.parent = None
        self.children = children
        self.bot = None
        self.alignment_len = alignment_len
        wrapper = lambda u, c: self.display(get_message(u))
        self.handler = CallbackQueryHandler(handle_exception(wrapper), pattern=self.name)

    def register(self, bot):
        self.bot = bot
        logging.debug(f'register {self.display_name}, {self.name}')
        ChatMenuHandlers.add_handler(bot, self.chat_id, self.handler)

        for c in self.children:
            c.parent = self
            c.register(bot)

    def unregister(self):
        logging.debug(f'unregister {self.display_name}')
        self.bot.updater.dispatcher.remove_handler(self.handler)

        for c in self.children:
            c.unregister()

    def display(self, message):
        logging.debug(f'self.display_name {self.display_name}, self.keyboard() {self._keyboard(self.children)}')
        message.edit_text(self.display_name, reply_markup=self._keyboard(self.children))

    def create(self, message):
        message.reply_text(self.display_name, reply_markup=self._keyboard(self.children))

    @staticmethod
    def help():
        pass

    def _keyboard(self, children):
        disp_len = 0
        res = []
        sub_res = []
        help_res = None
        bottom = []
        for c in children:
            if c.display_name == constants.M_HELP:
                help_res = InlineKeyboardButton(c.display_name, callback_data=c.name)
            else:
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
            bottom.append(InlineKeyboardButton(f'{constants.BACK_EMOJI} {constants.S_BACK_TO} {self.parent.display_name}',
                                               callback_data=self.parent.name))
        if help_res:
            bottom.append(help_res)

        res.append(bottom)

        return InlineKeyboardMarkup(res)


class MainMenu(Menu):
    @staticmethod
    def help():
        return constants.H_MAIN

    def display(self, message):
        logging.info(f'Loggining into "{self.display_name.capitalize()} account"')

        with ProgressBarWriter(message) as _:
            chain = get_chain_instance(message.chat_id, self.chain_cls)

            children = []
            for c in self.children:
                if c.display_name != constants.M_CHECKOUT or chain.get_current_slot():
                    children.append(c)

            m_help = HelpMenu(self.chat_id, self.chain_cls, constants.M_HELP, [])
            m_help.parent = self
            m_help.register(self.bot)
            children.append(m_help)

        logging.debug(f'self.display_name {self.display_name}, self.keyboard() {self._keyboard(children)}')

        message.edit_text(self.display_name, reply_markup=self._keyboard(children))

    @staticmethod
    def help():
        return constants.H_MAIN


class CheckoutMenu(Menu):
    def register(self, bot):
        self.parent = self.parent.parent
        super().register(bot)

    def _create_slot_menu(self, message):
        logging.debug(f'self.display_name {self.display_name}, self.keyboard() {self._keyboard(self.children)}')

        chain = get_chain_instance(message.chat_id, self.chain_cls)
        cur_slot = chain.get_current_slot()

        children = []

        if not cur_slot:
            raise ValueError(constants.E_SLOT_EXPIRED)

        m_slot = CheckoutSlotMenu(self.chat_id, self.chain_cls, get_pretty_slot_name(cur_slot, self.chain_cls), [])
        m_slot.register(self.bot)
        m_slot.parent = self.parent
        children.append(m_slot)

        # Help menu
        m_help = HelpMenu(self.chat_id, self.chain_cls, constants.M_HELP, [])
        m_help.parent = self
        m_help.register(self.bot)
        children.append(m_help)

        return children

    @asynchronous
    def display(self, message):
        m_slot = self._create_slot_menu(message)
        message.edit_text(self.display_name, reply_markup=self._keyboard(m_slot))

    @asynchronous
    def create(self, message):
        m_slot = self._create_slot_menu(message)
        message.reply_text(self.display_name, reply_markup=self._keyboard(m_slot))

    @staticmethod
    def help():
        return constants.H_CHECKOUT


class CheckoutSlotMenu(Menu):
    @asynchronous
    def display(self, message):
        logging.debug(f'self.display_name {self.display_name}, self.keyboard() {self._keyboard(self.children)}')

        chain = get_chain_instance(message.chat_id, self.chain_cls)
        cur_slot = chain.get_current_slot()

        if not cur_slot:
            raise ValueError(constants.E_SLOT_EXPIRED)

        res = chain.checkout(Settings(message.chat_id, self.chain_cls.name).cvv)

        disp_name = f"Slot {self.display_name} is {constants.S_CHECKED_OUT}. {constants.S_ORDER_NUMBER} {res}"
        message.edit_text(disp_name, reply_markup=self._keyboard([]))


class SettingsMenu(Menu):
    def display(self, message):
        logging.debug(f'self.display_name {self.display_name}, self.keyboard() {self._keyboard(self.children)}')

        # Help menu
        m_help = HelpMenu(self.chat_id, self.chain_cls, constants.M_HELP, [])
        m_help.parent = self
        m_help.register(self.bot)
        self.children.append(m_help)

        message.edit_text(self.display_name, reply_markup=self._keyboard(self.children))

    @staticmethod
    def help():
        return constants.H_SETTINGS


class HelpMenu(Menu):
    @asynchronous
    def display(self, message):
        disp_name = self.parent.help()
        message.edit_text(disp_name, reply_markup=self._keyboard([]))

# a decorator to catch unhandled exceptions
import sys
import telegram
import logging
from app.log import app_exception
from app.log.status_bar import PROGRESS_LOG, StatusBarWriter
from app.constants import LOG_CHAT_ID
import traceback


# used as a decorator for all menu display calls (handlers)
def handle_exception(fn):
    def inner(update_or_self, callback_or_message):
        if isinstance(update_or_self, telegram.Update):
            if update_or_self.message:
                bot = update_or_self.message.bot
                message = update_or_self.message
            else:
                bot = update_or_self.callback_query.bot
                message = update_or_self.callback_query.message
        else:
            bot = callback_or_message.bot
            message = callback_or_message

        try:
            return fn(update_or_self, callback_or_message)
        except telegram.error.TimedOut as ex:
            with StatusBarWriter(message) as _:
                logging.exception('Timeout occurred')
                txt = 'Timeout has occurred, please /start bot again'
                PROGRESS_LOG.info(txt)
                bot.send_message(chat_id=LOG_CHAT_ID,
                                 text=str(message.chat_id) + ': ' + txt)
        except app_exception.AppException as ex:
            with StatusBarWriter(message) as _:
                logging.exception(ex.internal_err_msg)
                PROGRESS_LOG.info(ex.user_err_msg)
                bot.send_message(chat_id=LOG_CHAT_ID,
                                 text=str(message.chat_id) + ': ' + ex.traceback)
        except:
            with StatusBarWriter(message) as _:
                logging.exception('Unexpected error occurred')
                PROGRESS_LOG.info('An error occurred, please try later or contact support @kapbka')
                bot.send_message(chat_id=LOG_CHAT_ID,
                                 text=str(message.chat_id) + ': ' + traceback.format_exc())

    return inner

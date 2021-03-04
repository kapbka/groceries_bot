# a decorator to catch unhandled exceptions
import sys
import telegram
import logging
from app.log import app_exception
from app.log.logger import PROGRESS_LOG, StatusBarWriter
from app.constants import LOG_CHAT_ID


# used as a decorator for all menu display calls (handlers)
def handle_exception(fn):
    def inner(update, callback):
        try:
            return fn(update, callback)
        except telegram.error.TimedOut as ex:
            with StatusBarWriter(update.callback_query.message) as _:
                logging.exception('Timeout occurred')
                txt = 'Timeout has occurred, please /start bot again'
                PROGRESS_LOG.info(txt)
                update.callback_query.bot.send_message(chat_id=LOG_CHAT_ID,
                                                       text=str(update.callback_query.message.chat_id) + ': ' + txt)
        except app_exception.LoginFailException as ex:
            with StatusBarWriter(update.callback_query.message) as _:
                logging.exception('Client error')
                PROGRESS_LOG.info(ex.user_err_msg)
                update.callback_query.bot.send_message(chat_id=LOG_CHAT_ID,
                                                       text=str(update.callback_query.message.chat_id) + ': ' + ex.traceback)
        except:
            with StatusBarWriter(update.callback_query.message) as _:
                ex_type, ex, tb = sys.exc_info()
                logging.exception('Unexpected error occurred')
                PROGRESS_LOG.info('An error occurred, please try later or contact support @kapbka')
                update.callback_query.bot.send_message(chat_id=LOG_CHAT_ID,
                                                       text=str(update.callback_query.message.chat_id) + ': ' + str(tb))

    return inner

# a decorator to catch unhandled exceptions
import telegram
import logging
from app.log import app_exception


# used as a decorator for all menu display calls (handlers)
def handle_exception(fn):
    def inner(update, callback):
        try:
            return fn(update, callback)
        except telegram.error.TimedOut as ex:
            logging.exception('Timeout occurred')
            update.callback_query.message.delete()
            update.callback_query.bot.send_message(chat_id=update.effective_chat.id,
                                                   text='Timeout has occurred, please /start bot again')
        except app_exception.LoginFailException as ex:
            logging.exception('Client error')
            update.callback_query.message.delete()
            update.callback_query.bot.send_message(chat_id=update.effective_chat.id,
                                                   text=ex.user_err_msg)
        except:
            logging.exception('Unexpected error occurred')
            update.callback_query.message.delete()
            update.callback_query.bot.send_message(chat_id=update.effective_chat.id,
                                                   text='An error occurred, please try later or contact support @kapbka')

    return inner

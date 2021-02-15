# a decorator to catch unhandled exceptions
import logging


def handle_exception(fn):
    def inner(update, callback):
        try:
            return fn(update, callback)
        except:
            logging.exception('Unexpected error occurred')
            update.callback_query.message.delete()
            update.callback_query.bot.send_message(chat_id=update.effective_chat.id,
                                                   text='An error occurred, please try later or contact support @kapbka')

    return inner

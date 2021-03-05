# logging

import logging
import time
from telegram import Message
from datetime import datetime
from logging import StreamHandler
from threading import Thread
from app.constants import EXL_MARK_EMOJI
import re


PROGRESS_LOG = logging.getLogger('telegram')
DOT_CNT = 5


class StatusBarWriter(StreamHandler):
    def __init__(self, message: Message):
        StreamHandler.__init__(self)
        self.message = message
        self.setLevel(logging.INFO)

        self.log = PROGRESS_LOG
        self.log.setLevel(logging.INFO)

        self.setFormatter(logging.Formatter('%(message)s'))
        self.log.addHandler(self)

    def emit(self, record):
        # rtrim any previous status in square bracets and add new information
        text = re.sub(': \\[.+?\\]', '', self.message.text) + ': [ ' + EXL_MARK_EMOJI + self.format(record) + ' ]'
        logging.debug(f'emit {text}')
        self.message.edit_text(text, reply_markup=self.message.reply_markup)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.log.removeHandler(self)


class ProgressBarWriter(StatusBarWriter):
    def __init__(self, message: Message):
        super().__init__(message)

        self.thread = Thread(target=self._worker_thread)
        self.is_running = True
        self.text = 'Loading'

    def _worker_thread(self):
        logging.debug(f'_worker_thread start, message_id {self.message.message_id}')
        curr_cnt = 1
        while self.is_running:
            try:
                if self.text:
                    if curr_cnt > DOT_CNT:
                        curr_cnt = 1
                    # rtrim any previous status in square bracets and add new information
                    txt = re.sub(': \\[.+?\\]', '', self.message.text) + ': [ ' + self.text + ' ' + '.' * curr_cnt + ' ' * (DOT_CNT - curr_cnt) + ' ]'
                    logging.debug(f'_worker_thread text {txt}')
                    if self.is_running:
                        self.message.edit_text(txt, reply_markup=self.message.reply_markup)
                    curr_cnt += 1
            except:
                logging.exception(f'_worker_thread fail')
            time.sleep(0.3)
        logging.debug(f'_worker_thread stop, message_id {self.message.message_id}')

    def emit(self, record):
        self.text = self.format(record)
        logging.debug(f'emit {self.text}')

    def __enter__(self):
        self.thread.start()
        return super().__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.is_running = False
        self.thread.join()
        super().__exit__(exc_type, exc_val, exc_tb)

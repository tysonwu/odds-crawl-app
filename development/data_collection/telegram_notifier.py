# -*- coding: utf-8 -*-
"""
Based on the tutorial:
https://www.marcodena.it/blog/telegram-logging-handler-for-python-java-bash/
"""

import requests
from logging import Handler, Formatter
import logging
import datetime
from telegram_tokens import users

user = users()
TELEGRAM_TOKEN = user.token
TELEGRAM_CHAT_ID = user.chat_id


class RequestsHandler(Handler):
    def emit(self, record):
        log_entry = self.format(record)
        payload = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': log_entry,
            'parse_mode': 'HTML'
        }
        return requests.post("https://api.telegram.org/bot{token}/sendMessage".format(token=TELEGRAM_TOKEN),
                             data=payload).content


class LogstashFormatter(Formatter):
    def __init__(self):
        super(LogstashFormatter, self).__init__()

    def format(self, record):
        t = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return "<i>{datetime}</i><pre>\n{message}</pre>".format(message=record.msg, datetime=t)


def notify(info): # receives a string
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.WARNING)
    
    handler = RequestsHandler()
    formatter = LogstashFormatter()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    logger.setLevel(logging.INFO)
    logger.info(info)
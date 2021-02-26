import logging
from mongoengine import connect as _mongo_connect


def connect():
    connection = _mongo_connect('groceries-bot', host='clrn.ddns.net', username='groceries-bot', password='Uw6q)3D;-w3wfnA#')
    logging.info(f"Connecting to {connection}")

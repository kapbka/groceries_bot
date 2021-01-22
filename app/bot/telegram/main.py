# main script to launch telegram bot

from app.bot.telegram.groceries_bot import GroceriesBot
import logging

BOT_TOKEN = '1579751582:AAEcot5v5NLyxXB1uFYQiBCyvBAsKOzGGsU'
CHAIN_LIST = ['waitrose', 'tesco'] # , 'coop', 'asda', 'lidl', 'sainsbury'

if __name__ == '__main__':
    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)
    b = GroceriesBot(BOT_TOKEN, CHAIN_LIST)
    b.run()

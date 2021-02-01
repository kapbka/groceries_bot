# main script to launch telegram bot

import logging
from app.waitrose.waitrose import Waitrose
from app.tesco.tesco import Tesco
from app.bot.telegram.groceries_bot import GroceriesBot


BOT_TOKEN = '1579751582:AAEcot5v5NLyxXB1uFYQiBCyvBAsKOzGGsU'
CHAIN_LIST = [Waitrose, Tesco] # , Coop, Asda, Lidl, Sainsbury

if __name__ == '__main__':
    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)
    b = GroceriesBot(BOT_TOKEN, CHAIN_LIST)
    b.run()

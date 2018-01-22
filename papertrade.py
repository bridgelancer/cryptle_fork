from datafeed import *
from strategy import *
from loglevel import *

import logging
import time
import sys

logger = logging.getLogger('Cryptle')
formatter = defaultFormatter()

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)

fh = logging.FileHandler('papertrade.log', mode='w')
fh.setLevel(logging.TRADE)
fh.setFormatter(formatter)

logger.addHandler(fh)
logger.addHandler(ch)


def papertrade():
    logger.debug("Initialising BitstampFeed")
    bs = BitstampFeed()

    logger.debug("Initialising portfolio")
    port1 = Portfolio(10000)
    port2 = Portfolio(10000)

    logger.debug("Initialising strategies")

    wmabch_3m  = WMAForceBollingerStrat('bchusd', port2, message='[3m]', period=180)
    wmabch_3m.equity_at_risk = 1

    logger.debug("Setting up callbacks")
    bs.onTrade('bchusd', wmabch_3m)

    bs.onTrade('bchusd', lambda x: logger.log(logging.TICK, x))

    logger.debug("Reporting...")

    while bs.isConnected():
        logger.info('Five min WMA_mod Cash:   %.2f' % port1.cash)
        logger.info('Five min WMA_mod Assets: %s' % str(port1.balance))

        logger.info('Three min WMA_mod Cash:   %.2f' % port2.cash)
        logger.info('Three min WMA_mod Assets: %s' % str(port2.balance))

        time.sleep(120)


if __name__ == '__main__':
    papertrade()


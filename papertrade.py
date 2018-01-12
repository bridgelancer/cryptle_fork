from bitstamp import *
from strategy import *

import logging
import time
import sys

# Set new log levels
logging.TRADE = 5
logging.TA = 9

logging.addLevelName(logging.TRADE, 'TRADE')
logging.addLevelName(logging.TA, 'TA')

logger = logging.getLogger('Cryptle')
logger.setLevel(1)

formatter = logging.Formatter('%(name)s: %(asctime)s [%(levelname)s] %(message)s', '%Y-%m-%d %H:%M:%S')

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
    wmaeth_5m  = WMAModStrat('ethusd', port1, message='[5m]', period=300)
    wmabtc_5m  = WMAModStrat('btcusd', port1, message='[5m]', period=300)
    wmaxrp_5m  = WMAModStrat('xrpusd', port1, message='[5m]', period=300)
    wmabch_5m  = WMAModStrat('bchusd', port1, message='[5m]', period=300)

    wmaeth_3m  = WMAModStrat('ethusd', port2, message='[3m]', period=180)
    wmabtc_3m  = WMAModStrat('btcusd', port2, message='[3m]', period=180)
    wmaxrp_3m  = WMAModStrat('xrpusd', port2, message='[3m]', period=180)
    wmabch_3m  = WMAModStrat('bchusd', port2, message='[3m]', period=180)

    wmaeth_5m.equity_at_risk = 0.25
    wmabtc_5m.equity_at_risk = 0.25
    wmaxrp_5m.equity_at_risk = 0.25
    wmabch_5m.equity_at_risk = 0.25

    wmaeth_3m.equity_at_risk = 0.25
    wmabtc_3m.equity_at_risk = 0.25
    wmaxrp_3m.equity_at_risk = 0.25
    wmabch_3m.equity_at_risk = 0.25

    logger.debug("Setting up callbacks")
    bs.onTrade('ethusd', wmaeth_5m)
    bs.onTrade('btcusd', wmabtc_5m)
    bs.onTrade('xrpusd', wmaxrp_5m)
    bs.onTrade('bchusd', wmabch_5m)

    bs.onTrade('ethusd', wmaeth_3m)
    bs.onTrade('btcusd', wmabtc_3m)
    bs.onTrade('xrpusd', wmaxrp_3m)
    bs.onTrade('bchusd', wmabch_3m)

    logger.debug("Reporting...")
    while True:
        logger.info('Five min WMA_mod Cash:   %.2f' % port1.cash)
        logger.info('Five min WMA_mod Assets: %s' % str(port1.balance))

        logger.info('Three min WMA_mod Cash:   %.2f' % port2.cash)
        logger.info('Three min WMA_mod Assets: %s' % str(port2.balance))

        time.sleep(120)


if __name__ == '__main__':
    papertrade()


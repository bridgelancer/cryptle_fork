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
    port = Portfolio(10000)

    logger.debug("Initialising strategies")
    atreth  = ATRStrat('ethusd', port, message='', period=180)
    atrbtc  = ATRStrat('btcusd', port, message='', period=180)
    atrxrp  = ATRStrat('xrpusd', port, message='', period=180)
    atrbch  = ATRStrat('bchusd', port, message='', period=180)

    logger.debug("Setting up callbacks")
    bs.onTrade('ethusd', atreth)
    bs.onTrade('btcusd', atrbtc)
    bs.onTrade('xrpusd', atrxrp)
    bs.onTrade('bchusd', atrbch)

    logger.debug("Reporting...")
    while True:
        logger.info('Cash:   %.2f' % port.cash)
        logger.info('Assets: %s' % str(port.balance))
        logger.info('Equity: %.2f' % port.equity())

        logger.log(logging.TA, 'ETH ATR: %.2f' % atreth.bar.atr_val)
        logger.log(logging.TA, 'ETH MA:  %.2f' % atreth.five_min.avg)

        logger.log(logging.TA, 'BTC ATR: %.2f' % atrbtc.bar.atr_val)
        logger.log(logging.TA, 'BTC MA:  %.2f' % atrbtc.five_min.avg)

        logger.log(logging.TA, 'XRP ATR: %.2f' % atrxrp.bar.atr_val)
        logger.log(logging.TA, 'XRP MA:  %.2f' % atrxrp.five_min.avg)

        logger.log(logging.TA, 'BCH ATR: %.2f' % atrbch.bar.atr_val)
        logger.log(logging.TA, 'BCH MA:  %.2f' % atrbch.five_min.avg)

        time.sleep(60)


if __name__ == '__main__':
    papertrade()


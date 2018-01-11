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
    atreth  = ATRStrat('ethusd', port1, message='[VWMA]', period=180)
    atrbtc  = ATRStrat('btcusd', port1, message='[VWMA]', period=180)
    atrxrp  = ATRStrat('xrpusd', port1, message='[VWMA]', period=180)
    atrbch  = ATRStrat('bchusd', port1, message='[VWMA]', period=180)

    wmaeth  = WMAStrat('ethusd', port2, message='[WMA]', period=180)
    wmabtc  = WMAStrat('btcusd', port2, message='[WMA]', period=180)
    wmaxrp  = WMAStrat('xrpusd', port2, message='[WMA]', period=180)
    wmabch  = WMAStrat('bchusd', port2, message='[WMA]', period=180)

    atreth.equity_at_risk = 0.25
    atrbtc.equity_at_risk = 0.25
    atrxrp.equity_at_risk = 0.25
    atrbch.equity_at_risk = 0.25

    wmaeth.equity_at_risk = 0.25
    wmabtc.equity_at_risk = 0.25
    wmaxrp.equity_at_risk = 0.25
    wmabch.equity_at_risk = 0.25

    logger.debug("Setting up callbacks")
    bs.onTrade('ethusd', atreth)
    bs.onTrade('btcusd', atrbtc)
    bs.onTrade('xrpusd', atrxrp)
    bs.onTrade('bchusd', atrbch)
    bs.onTrade('ethusd', wmaeth)
    bs.onTrade('btcusd', wmabtc)
    bs.onTrade('xrpusd', wmaxrp)
    bs.onTrade('bchusd', wmabch)

    logger.debug("Reporting...")
    while True:
        logger.info('VWMA ATR Cash:   %.2f' % port1.cash)
        logger.info('VWMA ATR Assets: %s' % str(port1.balance))

        logger.info('WMA Cash:   %.2f' % port1.cash)
        logger.info('WMA Assets: %s' % str(port1.balance))

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


from bitstamp import *
from strategy import *

import logging
import time
import sys


logger = logging.getLogger('Cryptle')
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(name)s: %(asctime)s [%(levelname)s] %(message)s', '%Y-%m-%d %H:%M:%S')

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)

logger.addHandler(ch)


def main(pair='ethusd'):
    bs = BitstampFeed()

    port1 = Portfolio(10000)
    port2 = Portfolio(10000)
    port3 = Portfolio(10000)
    port4 = Portfolio(10000)
    port5 = Portfolio(10000)

    # Add a few more strat instances and tweak their parameters to test run
    rf   = RFStrat(pair, port2)
    atr1  = ATRStrat(pair, port3, 60)
    atr2  = ATRStrat(pair, port4, 180)

    atr3  = ATRStrat(pair, port3, 60)
    atr4  = ATRStrat(pair, port4, 180)

    atr3.timelag_required = 10
    atr4.timelag_required = 10

    bs.onTrade(pair, rf)
    bs.onTrade(pair, atr1)
    bs.onTrade(pair, atr2)
    bs.onTrade(pair, atr3)
    bs.onTrade(pair, atr4)

    while True:
        logger.info('RF Cash: '      + str(port1.cash))
        logger.info('RF Balance: '   + str(port1.balance))
        logger.info('ATR1 Cash: '    + str(port2.cash))
        logger.info('ATR1 Balance: ' + str(port2.balance))
        logger.info('ATR2 Cash: '    + str(port3.cash))
        logger.info('ATR2 Balance: ' + str(port3.balance))
        logger.info('ATR4 Cash: '    + str(port4.cash))
        logger.info('ATR3 Balance: ' + str(port4.balance))
        logger.info('ATR4 Cash: '    + str(port5.cash))
        logger.info('ATR4 Balance: ' + str(port5.balance))

        try:
            logger.info('ATR1 : ' + str(atr1.bar.getAtr()))
            logger.info('ATR2 : ' + str(atr2.bar.getAtr()))
            logger.info('ATR3 : ' + str(atr3.bar.getAtr()))
            logger.info('ATR4 : ' + str(atr4.bar.getAtr()))
        except:
            pass

        time.sleep(120)


if __name__ == '__main__':
    print('Hello crypto!')
    try:
        pair = sys.argv[1]

        fh = logging.FileHandler(pair + '.log', mode='w')
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

        main(pair)
    except:
        main()


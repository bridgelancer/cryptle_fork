from bitstamp import *
from strategy import *

import logging
import time
import sys


logger = logging.getLogger('Cryptle')
logger.setLevel(1)

formatter = logging.Formatter('%(name)s: %(asctime)s [%(levelname)s] %(message)s', '%Y-%m-%d %H:%M:%S')

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)

logger.addHandler(ch)


def main(pair='ethusd'):
    print("Initialising BitstampFeed")
    bs = BitstampFeed()

    print("Initialising portfolios")
    port1 = Portfolio(10000)
    port2 = Portfolio(10000)
    port3 = Portfolio(10000)
    port4 = Portfolio(10000)
    port5 = Portfolio(10000)

    print("Initialising strategies")
    atr1  = ATRStrat(pair, port2, message='[ATR1]', period=60)
    atr2  = ATRStrat(pair, port3, message='[ATR2]', period=180)

    atr3  = ATRStrat(pair, port4, message='[ATR3]', period=60)
    atr4  = ATRStrat(pair, port5, message='[ATR4]', period=180)
    atr3.timelag_required = 30
    atr4.timelag_required = 30

    print("Setting up callbacks")
    bs.onTrade(pair, lambda x: logger.log(0, x))
    bs.onTrade(pair, rf)
    bs.onTrade(pair, atr1)
    bs.onTrade(pair, atr2)
    bs.onTrade(pair, atr3)
    bs.onTrade(pair, atr4)

    print("Reporting...")
    while True:
        logger.info('RF Cash: '      + str(port1.cash))
        logger.info('RF Balance: '   + str(port1.balance))
        logger.info('ATR1 Cash: '    + str(port2.cash))
        logger.info('ATR1 Balance: ' + str(port2.balance))
        logger.info('ATR2 Cash: '    + str(port3.cash))
        logger.info('ATR2 Balance: ' + str(port3.balance))
        logger.info('ATR3 Cash: '    + str(port4.cash))
        logger.info('ATR3 Balance: ' + str(port4.balance))
        logger.info('ATR4 Cash: '    + str(port5.cash))
        logger.info('ATR4 Balance: ' + str(port5.balance))

        try:
            logger.debug('ATR1/3 : ' + str(atr1.bar.getAtr()))
            logger.debug('ATR2/4: ' + str(atr2.bar.getAtr()))
            logger.debug('5 min RF MA' + str(rf.five_min.avg))
            logger.debug('8 min RF MA' + str(rf.eight_min.avg))
            logger.debug('5 min ATR MA' + str(atr1.five_min.avg))
            logger.debug('8 min ATR MA' + str(atr1.eight_min.avg))
        except:
            pass

        time.sleep(60)


if __name__ == '__main__':
    try:
        pair = sys.argv[1]

        fh = logging.FileHandler(pair + '.log', mode='w')
        fh.setLevel(1)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

        print('Hello crypto!')
        main(pair)
    except:
        main()


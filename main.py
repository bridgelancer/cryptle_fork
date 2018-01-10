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

def readcsv(filename):	
    ifile = open(filename, "rU")
    reader = csv.reader(ifile, delimiter="\n")

    rownum = 0	
    ls = []

    for row in reader:
        a.append (row)
        rownum += 1
    
    ifile.close()
    return ls

def main(pair='ethusd'):
    bs = BitstampFeed()

    port1 = Portfolio(10000)
    port2 = Portfolio(10000)
    port3 = Portfolio(10000)
    port4 = Portfolio(10000)
    port5 = Portfolio(10000)

    # Add a few more strat instances and tweak their parameters to test run
    rf   = RFStrat(pair, port2)
    atr  = ATRStrat(pair, port3)

    bs.onTrade(pair, lambda x: logger.debug('Recieved new tick'))
    bs.onTrade(pair, atr)

    while True:
        logger.info('RF Cash: ' + str(port2.cash))
        logger.info('RF Balance: ' + str(port2.balance))
        logger.info('ATR Cash: ' + str(port3.cash))
        logger.info('ATR Balance: ' + str(port3.balance))

        logger.info('ATR val: ' + str(atr.bar.atr_val))
        logger.info('ls: ' + str(atr.bar.ls))
        logger.info('_bars: ' + str(atr.bar._bars))
        
        logger.error('5 WMA: ' + str(atr.bar.WMA))
        time.sleep(60)


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


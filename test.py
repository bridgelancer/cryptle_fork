from ta import *
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

fh = logging.FileHandler('test.log', mode='w')
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)

logger.addHandler(ch)
logger.addHandler(fh)

class TestStrat(Strategy):

    def __call__(self, tick):
        price, volume, timestamp = self.unpackTick(tick)
        self.buy(1, price, 'Testing Buy')
        self.sell(1, price, 'Testing Sell')


def testBuySell():
    port = Portfolio(1000)
    strat = Strategy('ethusd', port)
    strat.buy(1, 1)
    strat.sell(1, 1)


def testFunctor():
    port = Portfolio(1000)
    strat = TestStrat('ethusd', port)

    jsonstr = '{"price": 100, "amount": 1, "timestamp": 15411121919}'
    strat(jsonstr)


if __name__ == '__main__':
    testBuySell()
    testFunctor()

from ta import *
from bitstamp import *
from strategy import *

import logging
import time
import sys
import csv

logger = logging.getLogger('Cryptle')
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(name)s: %(asctime)s [%(levelname)s] %(message)s', '%Y-%m-%d %H:%M:%S')

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)

fh = logging.FileHandler('test.log', mode='w')
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)

logger.addHandler(ch)
logger.addHandler(fh)

bslog = logging.getLogger('Bitstamp')
bslog.setLevel(logging.DEBUG)
bslog.addHandler(ch)
bslog.addHandler(fh)


class TestStrat(Strategy):

    def __call__(self, tick):
        price, volume, timestamp = self.unpackTick(tick)
        self.buy(1, price, 'Testing Buy')
        self.sell(1, price, 'Testing Sell')

def readCSV(filename):
    ifile = open(filename, "rU")
    reader = csv.reader(ifile, delimiter = "\n")

    rownum = 0
    ls = []

    for row in reader:
        ls.append(row)
        rownum += 1
    ifile.close()
    return ls

def loadCSV(ls, Strat):
    strat = Strat
    for item in ls:
        tick = ''.join(item)
        Strat(tick)

def testLoadCSV():
    port = Portfolio(10000)
    test = TestStrat('ethusd', port)

    ls = readCSV('btc_sample')
    loadCSV(ls, test)       

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


def testBitstampFeed():
    feed = BitstampFeed()

    feed.onTrade('btcusd', lambda x: logger.debug('Recieved BTC tick'))
    feed.onTrade('xrpusd', lambda x: logger.debug('Recieved XRP tick'))
    feed.onTrade('ethusd', lambda x: logger.debug('Recieved ETH tick'))
    feed.onTrade('ltcusd', lambda x: logger.debug('Recieved ETH tick'))
    feed.onTrade('bchusd', lambda x: logger.debug('Recieved ETH tick'))

    time.sleep(10)
    feed.pusher.disconnect()
    logger.debug('Disconnected from Bitstamp WebSockets')


def testBitstampREST():
    bs = BitstampREST()
    logger.debug(bs.getTicker('btcusd'))


def testATR():
    feed = BitstampFeed()
    port = Portfolio(10000)

    atr = ATRStrat('btcusd', port)
    ls = readCSV('btc_sample')

    for item in ls:
        tick = ''.join(item)
        atr(tick)
        

if __name__ == '__main__':
    testATR()


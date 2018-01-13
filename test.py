from ta import *
from exchange import *
from bitstamp import *
from strategy import *

import math
import logging
import time
import sys
import csv

formatter = logging.Formatter('%(name)s: %(asctime)s [%(levelname)s] %(message)s', '%Y-%m-%d %H:%M:%S')

logger = logging.getLogger('Cryptle')
logger.setLevel(logging.DEBUG)

bslog = logging.getLogger('Bitstamp')
bslog.setLevel(1)

fh = logging.FileHandler('test.log', mode='w')
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)

bslog.addHandler(fh)
logger.addHandler(fh)


class TestStrat(Strategy):

    def __call__(self, tick):
        price, volume, timestamp = self.unpackTick(tick)
        self.buy(1, 'Testing Buy', price)
        self.sell(1, 'Testing Sell', price)


def testBuySell():
    port = Portfolio(1000)
    strat = Strategy('ethusd', port)
    strat.buy(1, price=1)
    strat.sell(1, price=1)


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

    time.sleep(3)
    feed.pusher.disconnect()
    logger.debug('Disconnected from Bitstamp WebSockets')


def testBitstampREST():
    bs = BitstampREST()
    logger.debug(bs.getTicker('btcusd'))


def testEquity():
    port  = Portfolio(1000)
    strat = Strategy('ethusd', port)

    strat.buy(2, price=100)
    logger.debug(strat.equity_at_risk * strat.equity())
    logger.debug(strat.equity())
    logger.debug(strat.portfolio.cash)

    assert strat.equity() == 1000
    assert strat.portfolio.cash == 800


def testEquity():
    port  = Portfolio(1000)
    strat = Strategy('ethusd', port)
    strat.buy(2, price=100)

    assert strat.equity() == 1000
    assert strat.portfolio.cash == 800


def testCVWMA():
    line = [(i, 1, i) for i in range(15)]
    quad = [(i, i+1, i) for i in range(15)]
    sine = [(math.sin(i), 1, i) for i in range(15)]

    thre_line = ContinuousVWMA(3)
    thre_quad = ContinuousVWMA(3)
    thre_sine = ContinuousVWMA(3)

    five_line = ContinuousVWMA(5)
    five_quad = ContinuousVWMA(5)
    five_sine = ContinuousVWMA(5)

    five_ma = []
    thre_ma = []
    for tick in line:
        thre_line.update(tick[0], tick[1], tick[2])
        five_line.update(tick[0], tick[1], tick[2])
        thre_ma.append(thre_line.avg)
        five_ma.append(five_line.avg)

    assert thre_ma[3] == 2
    assert five_ma[13] == 11
    thre_ma.clear()
    five_ma.clear()

    for tick in quad:
        thre_quad.update(tick[0], tick[1], tick[2])
        five_quad.update(tick[0], tick[1], tick[2])
        thre_ma.append(thre_quad.avg)
        five_ma.append(five_quad.avg)

    logger.debug(str(thre_ma[3]) + ' ' + str(thre_ma[8]) + ' ' + str(thre_ma[13]))
    logger.debug(str(five_ma[3]) + ' ' + str(five_ma[8]) + ' ' + str(five_ma[13]))
    thre_ma.clear()
    five_ma.clear()

    for tick in sine:
        five_sine.update(tick[0], tick[1], tick[2])
        thre_sine.update(tick[0], tick[1], tick[2])
        thre_ma.append(thre_sine.avg)
        five_ma.append(five_sine.avg)

    logger.debug(str(thre_ma[3]) + ' ' + str(thre_ma[8]) + ' ' + str(thre_ma[13]))
    logger.debug(str(five_ma[3]) + ' ' + str(five_ma[8]) + ' ' + str(five_ma[13]))


const = [(3, i) for i in range(1, 100)]
lin = [(i, i) for i in  range(1, 100)]
quad  = [(i**2, i) for i in range(1, 100)]


def testSMA():
    candle = CandleBar(1)
    sma = SMA(candle, 3)

    for tick in const:
        candle.update(tick[0], tick[1])
        if tick[1] < 5: continue
        else: assert sma.sma == 3

    for tick in lin:
        candle.update(tick[0], tick[1])
        if tick[1] < 5: continue
        else: assert sma.sma == tick[1] - 2


def testWMA():

    candle = CandleBar(1)   # 1 second bar
    wma = WMA(candle, 5)    # 5 bar look ac

    for tick in const:
        candle.update(tick[0], tick[1])

    assert wma.wma == 3

    for tick in lin:
        candle.update(tick[0], tick[1])

    assert wma.wma - (293 / 3) < 1e-5


def testVWMAStrat():
    port = Portfolio(1000)
    vwma = VWMAStrat('bchusd', port, '[VWMA]', period=30)

    bs = BitstampFeed()
    bs.onTrade('bchusd', vwma)

    time.sleep(600)


if __name__ == '__main__':
    testBuySell()
    testFunctor()
    testEquity()
    testCVWMA()
    testSMA()
    testWMA()

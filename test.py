from ta import *
from exchange import *
from datafeed import *
from strategy import *

import math
import logging
import time
import sys
import csv

fmt = '%(name)8s| %(asctime)s [%(levelname)-5s] %(message)s'
formatter = logging.Formatter(fmt, '%Y-%m-%d %H:%M:%S')

logger = logging.getLogger('Cryptle')
logger.setLevel(logging.DEBUG)

bslog = logging.getLogger('Exchange')
bslog.setLevel(4)

fh = logging.FileHandler('test.log', mode='w')
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)

bslog.addHandler(fh)
logger.addHandler(fh)


class TestStrat(Strategy):

    def __call__(self, tick):
        price, volume, timestamp = self.unpackTick(tick)
        self.marketBuy(1, 'Testing Buy')
        self.marketSell(1, 'Testing Sell')


def testFunctor():
    port = Portfolio(1000)
    strat = TestStrat('ethusd', port)

    jsonstr = '{"price": 100, "amount": 1, "timestamp": 15411121919}'
    strat(jsonstr)


def testBitstampFeed():
    feed = BitstampFeed()
    time.sleep(1)

    feed.onTrade('btcusd', lambda x: logger.debug('Recieved BTC tick'))
    feed.onTrade('xrpusd', lambda x: logger.debug('Recieved XRP tick'))
    feed.onTrade('ethusd', lambda x: logger.debug('Recieved ETH tick'))
    feed.onTrade('ltcusd', lambda x: logger.debug('Recieved ETH tick'))
    feed.onTrade('bchusd', lambda x: logger.debug('Recieved ETH tick'))

    time.sleep(5)

    feed.pusher.disconnect()
    logger.debug('Disconnected from Bitstamp WebSockets')


def testBitstampREST():
    bs = Bitstamp()
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
    port  = Portfolio(10000)

    port.deposit('ethusd', 10, 1300)
    assert port.equity() == 23000

    port.withdraw('ethusd', 5)
    assert port.equity() == 16500

    port.deposit('ethusd', 5, 1000)
    assert port.equity() == 21500

    port.withdraw('ethusd', 10)
    assert port.equity() == 10000


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


def testEMA():
    candle = CandleBar(1)
    ema = EMA(candle, 3)

    for tick in const:
        candle.update(tick[0], tick[1])
        print(ema.ema)

    print("\n")

    for tick in lin:
        candle.update(tick[0], tick[1])
        print(ema.ema)



def testWMA():

    candle = CandleBar(1)   # 1 second bar
    wma = WMA(candle, 5)    # 5 bar look ac

    for tick in const:
        candle.update(tick[0], tick[1])

    assert wma.wma == 3

    for tick in lin:
        candle.update(tick[0], tick[1])

    assert wma.wma - (293 / 3) < 1e-5


if __name__ == '__main__':
    testEMA()

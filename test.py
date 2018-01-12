from ta import *
from bitstamp import *
from strategy import *

import math
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

# Return a list ls, containing json ticks in entries
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

# Parse the list ls into a Strategy class, tick by tick
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

def testParseTick(pair):
    ls = readCSV('tick_btc_json.log')

    result = []

    for tick in ls:
        tick = ''.join(tick)
        parsed_tick = json.loads(tick)
        price = parsed_tick['price']

        if pair == 'ethusd' and  900 < price < 1700:
            result.append(tick)
        elif pair == 'xrpusd' and  price < 3:
            result.append(tick)
        elif pair == 'btcusd' and price > 9000:
            result.append(tick)
        elif pair == 'bchusd' and  2000 < price < 3000:
            result.append(tick)

    return result

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

    time.sleep(5)
    feed.pusher.disconnect()
    logger.debug('Disconnected from Bitstamp WebSockets')


def testBitstampREST():
    bs = BitstampREST()
    logger.debug(bs.getTicker('btcusd'))


def testWMAModStrategy(pair):
    feed = BitstampFeed()
    port = Portfolio(2500)
    wmaeth  = WMAModStrat(str(pair), port, message='[WMA Mod]', period=180)
    wmaeth.equity_at_risk = 1.0

    ls = testParseTick(pair)
    loadCSV(ls, wmaeth)

    for item in ls:
        tick = ''.join(item)
        wmaeth(tick)
    
    logger.info('WMA Cash:   %.2f' % port.cash)
    logger.info('WMA Assets: %s' % str(port.balance))


def testWMAStrategy(pair):
    feed = BitstampFeed()
    port = Portfolio(2500)

    wmaeth  = WMAStrat(str(pair) , port, message='[WMA]', period=180)
    wmaeth.equity_at_risk = 1.0

    ls = testParseTick(pair)
    loadCSV(ls, wmaeth)

    for item in ls:
        tick = ''.join(item)
        wmaeth(tick)
    
    logger.info('WMA Cash:   %.2f' % port.cash)
    logger.info('WMA Assets: %s' % str(port.balance))

def testMA():
    line = [(i, 1, i) for i in range(15)]
    quad = [(i, i+1, i) for i in range(15)]
    sine = [(math.sin(i), 1, i) for i in range(15)]

    thre_line = MovingWindow(3)
    thre_quad = MovingWindow(3)
    thre_sine = MovingWindow(3)

    five_line = MovingWindow(5)
    five_quad = MovingWindow(5)
    five_sine = MovingWindow(5)

    five_ma = []
    thre_ma = []
    for tick in line:
        thre_line.update(tick[0], tick[1], tick[2])
        five_line.update(tick[0], tick[1], tick[2])
        thre_ma.append(thre_line.avg)
        five_ma.append(five_line.avg)

    logger.debug(str(thre_ma[3]) + ' ' + str(thre_ma[8]) + ' ' + str(thre_ma[13]))
    logger.debug(str(five_ma[3]) + ' ' + str(five_ma[8]) + ' ' + str(five_ma[13]))
    assert thre_ma[3] == 2
    assert five_ma[13] == 11

    thre_ma = []
    five_ma = []
    for tick in quad:
        thre_quad.update(tick[0], tick[1], tick[2])
        five_quad.update(tick[0], tick[1], tick[2])
        thre_ma.append(thre_quad.avg)
        five_ma.append(five_quad.avg)

    logger.debug(str(thre_ma[3]) + ' ' + str(thre_ma[8]) + ' ' + str(thre_ma[13]))
    logger.debug(str(five_ma[3]) + ' ' + str(five_ma[8]) + ' ' + str(five_ma[13]))

    thre_ma = []
    five_ma = []
    for tick in sine:
        five_sine.update(tick[0], tick[1], tick[2])
        thre_sine.update(tick[0], tick[1], tick[2])
        thre_ma.append(thre_sine.avg)
        five_ma.append(five_sine.avg)

    logger.debug(str(thre_ma[3]) + ' ' + str(thre_ma[8]) + ' ' + str(thre_ma[13]))
    logger.debug(str(five_ma[3]) + ' ' + str(five_ma[8]) + ' ' + str(five_ma[13]))

def testEquity():
    port  = Portfolio(1000)
    strat = Strategy('ethusd', port)

    strat.buy(2, 100)
    logger.debug(strat.equity_at_risk * strat.equity())
    logger.debug(strat.equity())
    logger.debug(strat.portfolio.cash)

    assert strat.equity() == 1000
    assert strat.portfolio.cash == 800

if __name__ == '__main__':
    #testBitstampFeed()
    pair = sys.argv[1]
    testWMAStrategy(pair)
    testWMAModStrategy(pair)




    



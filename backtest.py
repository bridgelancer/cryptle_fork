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

fh = logging.FileHandler('backtest.log', mode='w')
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)

logger.addHandler(ch)
logger.addHandler(fh)

bslog = logging.getLogger('Bitstamp')
bslog.setLevel(logging.DEBUG)
bslog.addHandler(ch)
bslog.addHandler(fh)

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
    ls = readCSV('tick_01121712.log')

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


def testWMAModStrategy(pair):
    feed = BitstampFeed()
    port = Portfolio(2500)
    wmaeth  = WMAModStrat(str(pair), port, message='[WMA Mod]', period=180)
    wmaeth.equity_at_risk = 1.0

    ls = testParseTick(pair)
    loadCSV(ls, wmaeth)

    logger.info('WMA Cash:   %.2f' % port.cash)
    logger.info('WMA Assets: %s' % str(port.balance))


def testWMAStrategy(pair):
    feed = BitstampFeed()
    port = Portfolio(2500)

    wmaeth  = WMAStrat(str(pair) , port, message='[WMA]', period=180)
    wmaeth.equity_at_risk = 1.0

    ls = testParseTick(pair)
    loadCSV(ls, wmaeth)

    logger.info('WMA Cash:   %.2f' % port.cash)
    logger.info('WMA Assets: %s' % str(port.balance))

def testSnoopingLoop(pair):
    strats = []
    ports = []

    snooping = range(60, 1800, 60)
    # Loop throug 5-100; 2-20
    for period in snooping:
        ports.append(Portfolio(1000))
        strats.append(WMAModStrat(str(pair), ports[snooping.index(period)], '[WMA {} min bar]'.format(period), period))

    for strat in strats:
        strat.equity_at_risk = 1.0

        ls = testParseTick(pair)
        loadCSV(ls, strat)
    
    for port in ports:
        logger.info('Port' + str(ports.index(port)) + ' cash: %.2f' % port.cash)
        logger.info("Port" + str(ports.index(port)) + ' balance : %s' % str(port.balance))


if __name__ == '__main__':
    pair = sys.argv[1]
    testSnoopingLoop(pair)
from ta import *
from datafeed import *
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
    ls = readCSV('bch.log')

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


def testVWMAStrat():
    port = Portfolio(1000)
    vwma = VWMAStrat('bchusd', port, '[VWMA]', period=30)

    bs = BitstampFeed()
    bs.onTrade('bchusd', vwma)

    time.sleep(60)


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

    snooping = range(60, 1860, 60)
    # Loop throug 60-1800 seconds bar, in 60s interval
    for period in snooping:
        ports.append(Portfolio(1000))
        strats.append(WMAModStrat(str(pair), ports[snooping.index(period)], '[WMA {} min bar]'.format(period), period))

    for strat in strats:
        strat.equity_at_risk = 1.0

        ls = testParseTick(pair)
        loadCSV(ls, strat)

    for port in ports:
        logger.info('Port' + str((ports.index(port) + 1)*60) + ' cash: %.2f' % port.cash)
        logger.info("Port" + str((ports.index(port) + 1)*60) + ' balance : %s' % str(port.balance))

# Enable snooping in two factor mode
# Caution: This function may run in extended period of time.
# The typical run time for an one day tick data feeding into 100 strategies is 1 minute.
def testSnoopingLoopN(pair):

    S = []
    P = []

    strats = []
    ports = []

    # Currently at least run 2*2 strats needed
    lags = range(350, 502, 150)
    snooping = range(180, 1860, 120)
    y = [x/1000 for x in lags]


    for lag in lags:
        for period in snooping:
            ports.append(Portfolio(1000))

            strat = WMAModStrat(str(pair), ports[snooping.index(period)], '[WMA {} min bar {}% ATR]'.format(period, y[lags.index(lag)]*100), period)
            strat.upper_atr = y[lags.index(lag)]
            strat.lower_atr = y[lags.index(lag)]
            strats.append(strat)

        S.append([x for x in strats])
        P.append([x for x in ports])

        strats.clear()
        ports.clear()

    for strats in S:
        for strat in strats:
            strat.equity_at_risk = 1.0

            ls = testParseTick(pair)
            loadCSV(ls, strat)

    for ports in P:
        for port in ports:
            if (len(snooping) or len(y) != 0):
                logger.info('Port' + str(snooping[0] + (snooping[1]-snooping[0])*ports.index(port)) + ' %.2f cash: %.2f' % (y[0] + ((y[1]-y[0])*(P.index(ports))), port.cash))
                logger.info("Port" + str(snooping[0] + (snooping[1]-snooping[0])*ports.index(port)) + ' %.2f  balance : %s' % (y[0]+ ((y[1]-y[0])*P.index(ports)), str(port.balance)))
            else:
                logger.info("Please loop at least two configs per factor")

def testMACD(pair):
    port = Portfolio(1000)
    macd = MACDStrat2(pair, port, message='[MACD]', period=120)

    ticks = testParseTick(pair)
    loadCSV(ticks, macd)

    logger.info('MACD Cash:   %.2f' % port.cash)
    logger.info('MACD Asset:  %s'   % str(port.cash))


if __name__ == '__main__':
    pair = sys.argv[1]
    testMACD(pair)

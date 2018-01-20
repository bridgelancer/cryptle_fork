from ta import *
from datafeed import *
from strategy import *

import subprocess
import math
import logging
import time
import sys
import csv
import itertools

logger = logging.getLogger('Cryptle')
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(name)s: %(asctime)s [%(levelname)s] %(message)s', '%Y-%m-%d %H:%M:%S')

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)

fh = logging.FileHandler('Snooping.log', mode='w')
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)

logger.addHandler(ch)
logger.addHandler(fh)

bslog = logging.getLogger('Bitstamp')
bslog.setLevel(logging.DEBUG)
bslog.addHandler(ch)
bslog.addHandler(fh)

def readJSON(filename):
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
def loadJSON(ls, Strat):
    strat = Strat
    for item in ls:
        tick = ''.join(item)
        Strat(tick)


def testloadJSON():
    port = Portfolio(10000)
    test = TestStrat('ethusd', port)

    ls = readJSON('btc_sample')
    loadJSON(ls, test)


def testParseTick(pair):
    ls = readJSON('papertrade0114p.log')

    result = []

    for tick in ls:
        tick = ''.join(tick)
        parsed_tick = json.loads(tick)
        price = parsed_tick['price']

        if pair == 'ethusd' and  900 < price < 1400:
            result.append(tick)
        elif pair == 'xrpusd' and  price < 3:
            result.append(tick)
        elif pair == 'btcusd' and price > 9000:
            result.append(tick)
        elif pair == 'bchusd' and  1600 < price < 3000:
            result.append(tick)

    return result


def testVWMAStrat():
    port = Portfolio(1000)
    vwma = VWMAStrat('bchusd', port, message='[VWMA]', period=30)

    bs = BitstampFeed()
    bs.onTrade('bchusd', vwma)

    time.sleep(60)


def testWMAModStrategy(pair):
    feed = BitstampFeed()
    port = Portfolio(1000)
    wmaeth  = WMAModStrat(str(pair), port, message='[WMA Mod]', period=180)
    wmaeth.equity_at_risk = 1.0

    ls = testParseTick(pair)
    loadJSON(ls, wmaeth)

    logger.info('WMA Equity:   %.2f' % port.equity())
    logger.info('WMA Cash:   %.2f' % port.cash)
    logger.info('WMA Assets: %s' % str(port.balance))

def testWMAForceStrategy(pair):
    feed = BitstampFeed()
    port = Portfolio(1000)
    paper = PaperExchange(0.0012)
    wmaeth  = WMAForceStrat(str(pair), port, exchange=paper, message='[WMA Force]', period=180)
    wmaeth.equity_at_risk = 1.0

    ls = testParseTick(pair)
    loadJSON(ls, wmaeth)

    logger.info('WMA Equity:   %.2f' % port.equity())
    logger.info('WMA Cash:   %.2f' % port.cash)
    logger.info('WMA Assets: %s' % str(port.balance))

from plotting import *

def testWMAForceBollingerStrategy(pair):
    feed = BitstampFeed()
    port = Portfolio(1000)
    paper = PaperExchange(0.0012)
    wmaeth  = WMAForceBollingerStrat(str(pair), port, exchange=paper, message='[WMA Bollinger]', period=180)
    wmaeth.equity_at_risk = 1.0

    ls = testParseTick(pair)
    loadJSON(ls, wmaeth)

    logger.info('WMA Equity:   %.2f' % port.equity())
    logger.info('WMA Cash:   %.2f' % port.cash)
    logger.info('WMA Assets: %s' % str(port.balance))

    # get back the candle bar
    # call script from python
    # put to plot
    candle = wmaeth.bar
    res = subprocess.run('./log_parser.sh', stdout=subprocess.PIPE)
    res = res.stdout.decode('utf-8')
    res = res.split('\n')
    res = [s.split(' ') for s in res]

    plotCandles(candle, trades=res)

def testWMAStrategy(pair):
    feed = BitstampFeed()
    port = Portfolio(1000)
    paper = PaperExchange(0.0012)

    wmaeth  = WMAStrat(str(pair) , port, exchange=paper, message='[WMA]', period=180)
    wmaeth.equity_at_risk = 1.0

    ls = testParseTick(pair)
    loadJSON(ls, wmaeth)

    logger.info('WMA Equity:   %.2f' % port.equity())
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
        loadJSON(ls, strat)

    for port in ports:
        logger.info('Port' + str((ports.index(port) + 1)*60) + ' cash: %.2f' % port.cash)
        logger.info("Port" + str((ports.index(port) + 1)*60) + ' balance : %s' % str(port.balance))

# This new function intends to snoop all the necessary parameters for a paritcular strategy on a single run. Needs to be implemented
def testSnoopingSuite(pair):
    period = range(3, 6, 2) # in minutes
    bband = range (300, 601, 10) # need to divide by 100
    timeframe = range(30, 181, 30)
    delay = range(0, 91, 30)
    upperatr = range(20, 81, 15) # need to divide by 100
    loweratr = range(20, 81, 15) # need to divide by 100
    bband_period = range (5, 31, 3)

    bband_100 = [x/100 for x in bband]
    upperatr_100 = [x/100 for x in upperatr]
    loweratr_100 = [x/100 for x in loweratr]
    # also snoop type of ma used for bars, bollinger band

    configs = itertools.product(period, bband_100, timeframe, delay, upperatr_100, loweratr_100, bband_period)

    strats = {}
    ports = {}

    for config in configs:
        period = config[0]
        bband = config[1]
        timeframe = config[2]
        delay = config[3]
        upperatr = config[4]
        loweratr = config[5]
        bband_period = config[6]



        ports[config] = Portfolio(1000)
        strat = WMAForceBollingerStrat(str(pair), ports[config], message='[WMA Force Bollinger]', period=period, bband_period=bband_period)

        strat.bband            = bband
        strat.timelag_required = timeframe
        strat.timelag_required = delay
        strat.upper_atr        = upperatr
        strat.lower_atr        = loweratr
        strat.equity_at_risk = 1.0

        strats[config] = strat

    ls = testParseTick(pair)
    # loop through strategies, and report balance
    for key in sorted(strats.keys()):
        loadJSON(ls, strats[key])
        print ('Strategy config %s' % str(key) + 'finished parsing')

    for key in sorted(ports.keys()):

        logger.info('Port' + str(key) + ' cash: %.2f' % ports[key].cash)
        logger.info("Port" + str(key) + ' balance : %s' % str(ports[key].balance))

    # one loop generate configs
    # another loop execute all the configs

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

            strat = WMAModStrat(str(pair), ports[snooping.index(period)], message='[WMA {} min bar {}% ATR]'.format(period, y[lags.index(lag)]*100), period=period)
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
            loadJSON(ls, strat)

    for ports in P:
        for port in ports:
            if (len(snooping) or len(y) != 0):
                logger.info('Port' + str(snooping[0] + (snooping[1]-snooping[0])*ports.index(port)) + ' %.2f cash: %.2f' % (y[0] + ((y[1]-y[0])*(P.index(ports))), port.cash))
                logger.info("Port" + str(snooping[0] + (snooping[1]-snooping[0])*ports.index(port)) + ' %.2f  balance : %s' % (y[0]+ ((y[1]-y[0])*P.index(ports)), str(port.balance)))
            else:
                logger.info("Please loop at least two configs per factor")

def testMACD(pair):
    port = Portfolio(1000)
    paper = PaperExchange(0.0012)
    macd = MACDStrat(pair, port, exchange=paper, message='[MACD]', period=180)
    macd.equity_at_risk = 1

    ticks = testParseTick(pair)
    loadJSON(ticks, macd)

    logger.info('MACD Equity: %.2f' % port.equity())
    logger.info('MACD Cash:   %.2f' % port.cash)
    logger.info('MACD Asset:  %s'   % str(port.cash))


def testSwiss(pair):
    port = Portfolio(10000)
    exchange = PaperExchange(0.0012)

    swiss = SwissStrat(pair, port, exchange=exchange, message='[Swiss]', period=180)
    swiss.equity_at_risk = 1

    ticks = testParseTick(pair)
    loadJSON(ticks, swiss)

    logger.info('Swiss Equity: %.2f' % port.equity())
    logger.info('Swiss Cash:   %.2f' % port.cash)
    logger.info('Swiss Asset:  %s'   % str(port.balance))
    logger.info('Swiss Balance_value:  %s'   % str(port.balance_value))


if __name__ == '__main__':
    pair = sys.argv[1]
    testSnoopingSuite(pair)

from ta import *
from datafeed import *
from strategy import *
from plotting import *
from loglevel import *

import matplotlib.pyplot as plt

import subprocess
import math
import logging
import time
import sys
import csv
import itertools
import random

logger = logging.getLogger('Cryptle')
logger.setLevel(logging.DEBUG)

formatter = defaultFormatter()

fh = logging.FileHandler('backtest.log', mode='w')
fh.setLevel(logging.INDEX)
fh.setFormatter(formatter)

logger.addHandler(fh)

bslog = logging.getLogger('Bitstamp')
bslog.setLevel(logging.INDEX)
bslog.addHandler(fh)


class Backtest():

    def run(self, strat):
        for tick in self.ticks:
            strat(tick)

    # Read file, detect it's data format and automatically parses it
    def read(self, fname, fileformat=None, fmt=None):
        raw = self._read(fname)
        fileformat = fileformat or self._guessFileType(raw[0])

        if fileformat == 'JSON':
            self.readJSON(fname)
        elif fileformat == 'CSV':
            self.readCSV(fname)
        elif fileformat == 'XML': # Not supported
            self.readString(fname)
        else:
            self.readString(fname)

    # Store ticks as list of strings
    def readString(self, fname):
        self.ticks = self._read(fname)

    # Not needed, Strategy now only supports json string
    def readJSON(self, fname):
        raw = self._read(fname)
        self.ticks = self._parseJSON(raw)

    # Not needed, Strategy now only supports json string
    def readCSV(self, fname, fieldnames=None):
        fieldnames = fieldnames or ['amount', 'price', 'timestamp']
        with open(fname) as f:
            reader = csv.DictReader(f, fieldnames=fieldnames)
            self.ticks = [row for row in reader]

    @staticmethod
    def _guessFileType(line):
        if line[0] == '{' or line[0] == '[':
            return 'JSON'
        elif line[0] == '<':
            return 'XML'
        elif ',' in line:
            return 'CSV'
        else:
            return None

    @staticmethod
    def _read(fname):
        with open(fname) as f:
            return f.read().splitlines()

    @staticmethod
    def _parseJSON(strings):
        return [json.loads(tick) for tick in strings]

    @staticmethod
    def _parseCSV(strings, fieldnames=None):
        x = []
        for s in strings:
            tx = {}
            s = s.split('n')
            for i, c in enumerate(s):
                tx[fieldnames[i]] = c


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

def parseJSON(pair):
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

    ls = parseJSON(pair)
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

    ls = parseJSON(pair)
    loadJSON(ls, wmaeth)

    logger.info('WMA Equity:   %.2f' % port.equity())
    logger.info('WMA Cash:   %.2f' % port.cash)
    logger.info('WMA Assets: %s' % str(port.balance))


def testWMAForceBollingerStrategy(pair):
    feed = BitstampFeed()
    port = Portfolio(1000)
    paper = PaperExchange(0.0012)
    wmaeth  = WMAForceBollingerStrat(str(pair), port, exchange=paper, message='[WMA Bollinger]', period=180)
    wmaeth.equity_at_risk = 1.0

    ls = parseJSON(pair)
    loadJSON(ls, wmaeth)

    logger.info('WMA Equity:   %.2f' % port.equity())
    logger.info('WMA Cash:   %.2f' % port.cash)
    logger.info('WMA Assets: %s' % str(port.balance))

    # get back the candle bar
    # call script from python
    # put to plot
    plotCandles(wmaeth.bar, trades=wmaeth.trades, title='Final equity: ${}'.format(port.equity()))


def testWMAStrategy(pair):
    feed = BitstampFeed()
    port = Portfolio(1000)
    paper = PaperExchange(0.0012)

    wmaeth  = WMAStrat(str(pair) , port, exchange=paper, message='[WMA]', period=180)
    wmaeth.equity_at_risk = 1.0

    ls = parseJSON(pair)
    loadJSON(ls, wmaeth)

    logger.info('WMA Equity:   %.2f' % port.equity())
    logger.info('WMA Cash:   %.2f' % port.cash)
    logger.info('WMA Assets: %s' % str(port.balance))


# This new function intends to snoop all the necessary parameters for a paritcular strategy on a single run. Already functioning
# Caution: This function may run in extended period of time.
def testSnoopingSuite(pair):

    # Datatypes to snoop
    period = range(3, 6, 2) # need to multiply by 60
    bband = range (300, 601, 10) # need to divide by 100
    timeframe = range(0, 181, 30) # need to multiply by 60
    delay = range(0, 91, 30) # (0, 91, 30)
    upperatr = range(50, 51, 15) # need to divide by 100
    loweratr = range(50, 51, 15) # need to divide by 100
    bband_period = range (5, 31, 5)

    period_60 = [x*60 for x in period]
    timeframe_60 = [x*60 for x in timeframe]
    bband_100 = [x/100 for x in bband]
    upperatr_100 = [x/100 for x in upperatr]
    loweratr_100 = [x/100 for x in loweratr]
    # @TODO also snoop type of ma used for bars, bollinger band

    configs = itertools.product(period_60, bband_100, timeframe_60, delay, upperatr_100, loweratr_100, bband_period)

    strats = {}
    ports = {}

    # Generating configs of strategies
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
        strat.timeframe        = timeframe
        strat.timelag_required = delay
        strat.upper_atr        = upperatr
        strat.lower_atr        = loweratr
        strat.equity_at_risk = 1.0

        strats[config] = strat

    counter = 0
    # load tick data to ls once only
    ls = parseJSON(pair)
    # feed tick data through strategies, and report the equity value of portfolio after finish parsing
    for key in sorted(strats.keys()):
        # the keys for the strats are the strategy config
        loadJSON(ls, strats[key])
        logger.info('Port' + str(key) + ' equity: %.2f' % strats[key].portfolio.equity())

        counter = counter + 1
        if counter%100 == 0:
            print ('%i Strategy configs' % counter + ' finished parsing')

        del strats[key] # optimize memory usage
        del ports[key]

# generate continuous data - random sampling of all ranges
def testSnoopingSuiteR(pair, runs):

    strats = {}
    ports = {}

    # Generating configs of strategies
    for run in range(0, runs):
        period = random.randrange(60, 240) # only as integer
        bband = random.uniform(1.5, 4)
        timeframe = random.randrange(0, 7200, 180)
        delay = random.randrange(0, 20)
        upperatr = 0.5
        loweratr = random.uniform(0.4, 0.5)
        bband_period = random.randrange(5, 20) # only as intenger

        # Generate tuple of config as the key of strategy and its associated portfolio
        config = (period, bband, timeframe, delay, upperatr, loweratr, bband_period)

        ports[config] = Portfolio(1000)
        strat = WMAForceBollingerStrat(str(pair), ports[config], message='[WMA Force Bollinger]', period=period, bband_period=bband_period)

        strat.bband            = bband
        strat.timeframe        = timeframe
        strat.timelag_required = delay
        strat.upper_atr        = upperatr
        strat.lower_atr        = loweratr
        strat.equity_at_risk = 1.0

        strats[config] = strat

    counter = 0
    # load tick data to ls once
    ls = parseJSON(pair)
    # feed tick data through strategies, and report after finish parsing
    for key in sorted(strats.keys()):
        loadJSON(ls, strats[key])
        logger.info('Port' + str(key) + ' equity: %.2f' % strats[key].portfolio.equity())

        counter = counter + 1
        if counter%100 == 0:
            print ('%i Strategy configs' % counter + ' finished parsing')

        del strats[key]
        del ports[key]

def testMACD(pair):
    port = Portfolio(1000)
    paper = PaperExchange(0.0012)
    macd = MACDStrat(pair, port, exchange=paper, message='[MACD]', period=180)
    macd.equity_at_risk = 1

    ticks = parseJSON(pair)
    loadJSON(ticks, macd)

    logger.info('MACD Equity: %.2f' % port.equity())
    logger.info('MACD Cash:   %.2f' % port.cash)
    logger.info('MACD Asset:  %s'   % str(port.cash))


def testSwiss(pair):
    port = Portfolio(10000)
    exchange = PaperExchange(0.0012)

    swiss = SwissStrat(pair, port, exchange=exchange, message='[Swiss]', period=180)
    swiss.equity_at_risk = 1

    ticks = parseJSON(pair)
    loadJSON(ticks, swiss)

    logger.info('Swiss Equity: %.2f' % port.equity())
    logger.info('Swiss Cash:   %.2f' % port.cash)
    logger.info('Swiss Asset:  %s'   % str(port.balance))
    logger.info('Swiss Balance_value:  %s'   % str(port.balance_value))

    plotCandles(swiss.candle, trades=swiss.trades, title='Final equity: ${}'.format(port.equity()))


# @Temporary
def demoBacktest(dataset, pair):
    test = Backtest()
    test.readString(dataset)

    port = Portfolio(10000)
    strat = WMAForceBollingerStrat(pair, port)

    test.run(strat)
    plotCandles(strat.bar)


if __name__ == '__main__':
    testWMAForceBollingerStrategy('bchusd')
    plt.show()

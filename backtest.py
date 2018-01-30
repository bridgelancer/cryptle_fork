from cryptle.backtest import *
from cryptle.strategy import Strategy, Portfolio
from cryptle.loglevel import *
from cryptle.plotting import *

import logging
import time
import sys
import itertools
import random


logger = logging.getLogger('Backtest')
logger.setLevel(logging.DEBUG)

formatter = defaultFormatter()

fh = logging.FileHandler('snoop_rsiobc_1.log', mode='w')
fh.setLevel(logging.INDEX)
fh.setFormatter(formatter)

logger.addHandler(fh)


def snoop(Strat, pair, dataset, **kws):
    '''Snoop necessary parameters for a paritcular strategy on a single run.

    Caution: This function may run in extended period of time.
    '''

    # Parameters to snoop
    period          = range(90, 181, 30)
    bband           = range(400, 1201, 50)  # need to divide by 100
    timeframe       = range(30, 91, 30)     # need to multiply by 60
    delay           = range(0, 31, 10)
    upperatr        = range(50, 51, 15)     # need to divide by 100
    loweratr        = range(50, 51, 15)     # need to divide by 100
    bband_period    = range(5, 41, 5)
    #vol_multiplier  = range(30, 31, 20)
    vol_multiplier   = [30]

    timeframe_60    = [x * 60 for x in timeframe]
    bband_100       = [x / 100 for x in bband]
    upperatr_100    = [x / 100 for x in upperatr]
    loweratr_100    = [x / 100 for x in loweratr]
    # @TODO also snoop type of ma used for bars, bollinger band

    configs = itertools.product(period, bband_100, timeframe_60, delay, upperatr_100, loweratr_100, bband_period, vol_multiplier)

    paper = PaperExchange(commission=0.0012, slippage=0)
    test = Backtest(paper)
    test.readJSON(dataset)

    # Run the config of strategies
    for i, config in enumerate(configs):
        period, bband, timeframe, delay, uatr, latr, bband_period, vol_multiplier = config

        port = Portfolio(10000)
        strat = Strat(
                period=period,
                upper_atr=uatr,
                lower_atr=latr,
                timeframe=timeframe,
                bband=bband,
                bband_period=bband_period,
                vol_multiplier=vol_multiplier,
                timelag_required=delay,
                pair=pair,
                portfolio=port,
                exchange=paper,
                equity_at_risk=1.0)
        test.run(strat)

        fmt = 'Port{} Equity: {:.2f} Trades: {}'
        logger.report(fmt.format(config, port.equity, len(strat.trades)))

        if i % 10 == 0:
            print('%i configs' % i + ' finished running')


def snoop_random(Strat, pair, dataset, runs, **kws):
    '''Randomly sample configurations of all ranges'''

    paper = PaperExchange(commission=0.0012, slippage=0)
    test = Backtest(paper)
    test.readJSON(dataset)

    # Generating configs of strategies
    for run in range(runs):
        period = random.randrange(60, 240) # only as integer
        bband = random.uniform(1.5, 4)
        timeframe = random.randrange(0, 7200, 180)
        delay = random.randrange(0, 20)
        upperatr = 0.5
        loweratr = random.uniform(0.4, 0.5)
        bband_period = random.randrange(5, 20) # only as intenger

        # Generate tuple of config as the key of strategy and its associated portfolio
        config = (period, bband, timeframe, delay, upperatr, loweratr, bband_period)

        port = Portfolio(10000)
        strat = Strat(pair=pair, portfolio=port, exchange=paper, period=period, bband_period=bband_period)

        strat.bband            = bband
        strat.timeframe        = timeframe
        strat.timelag_required = delay
        strat.upper_atr        = upperatr
        strat.lower_atr        = loweratr
        strat.equity_at_risk = 1.0

        test.run(strat)

        fmt = 'Port{} Equity: {:.2f} Trades: {}'
        logger.report(fmt.format(config, port.equity, len(strat.trades)))

        if run % 100 == 0:
            print ('%i Strategy configs' % run + ' finished parsing')


# @Temporary
def demoBacktest(dataset, pair):
    port = Portfolio(10000)
    exchange = PaperExchange(0.0012)
    strat = WMAForceBollingerStrat(pair=pair, portfolio=port, exchange=exchange)

    test = Backtest(exchange)
    test.readJSON(dataset)
    test.run(strat.tick)

    plotCandles(strat.bar)


def demoRSIStrat(dataset, pair):
    port = Portfolio(10000)
    exchange = PaperExchange(0.0012)
    strat = WMAForceBollingerRSIStrat(pair=pair, portfolio=port, exchange=exchange)

    test = Backtest(exchange)
    test.readJSON(dataset)
    test.run(strat.tick)

    plotCandles(strat.bar)


from wmabollingerrsi import WMAForceBollingerRSIStrat
from wmarsiobc import WMARSIOBCStrat

import matplotlib.pyplot as plt


if __name__ == '__main__':
    snoop(WMARSIOBCStrat, 'bchusd', 'data/bch_correct.log')

from cryptle.backtest import *
from cryptle.strategy import Portfolio
from cryptle.loglevel import *
#from cryptle.plotting import *

import logging
import time
import sys
import itertools
import random


formatter = defaultFormatter(notimestamp=True)

sh = logging.StreamHandler()
sh.setLevel(logging.REPORT)
sh.setFormatter(formatter)

fh = logging.FileHandler('backtest.1.log', mode='w')
fh.setLevel(logging.METRIC)
fh.setFormatter(formatter)

logger = logging.getLogger('Backtest')
logger.setLevel(logging.DEBUG)
logger.addHandler(sh)
logger.addHandler(fh)

stratlog = logging.getLogger('Strategy')
stratlog.setLevel(logging.METRIC)
stratlog.addHandler(fh)

baselog = logging.getLogger('cryptle')
baselog.setLevel(logging.METRIC)
baselog.addHandler(fh)


def snoop(Strat, dataset, pair, **kws):
    '''Snoop necessary parameters for a paritcular strategy on a single run.

    Caution: This function may run in extended period of time.
    '''

    # Parameters to snoop
    period          = range(30, 60, 10)
    bband           = range(850, 1201, 50)  # need to divide by 100
    timeframe       = range(60, 121, 30)     # need to multiply by 60
    bband_period    = range(10, 41, 10)

    timeframe_60    = [x * 60 for x in timeframe]
    bband_100       = [x / 100 for x in bband]
    # @TODO also snoop type of ma used for bars, bollinger band

    configs = itertools.product(period, bband_100, timeframe_60, bband_period)

    paper = PaperExchange(commission=0.0012, slippage=0)
    test = Backtest(paper)
    test.readJSON(dataset)

    # Run the config of strategies
    for i, config in enumerate(configs):
        period, bband, timeframe, bband_period = config

        port = Portfolio(10000)
        strat = Strat(
                period=period,
                upper_atr=0.5,
                lower_atr=0.5,
                timeframe=timeframe,
                bband=bband,
                bband_period=bband_period,
                pair=pair,
                portfolio=port,
                exchange=paper,
                equity_at_risk=1.0)
        test.run(strat)

        fmt = 'Port{} Equity: {:.2f} Trades: {}'
        logger.report(fmt.format(config, port.equity, len(strat.trades)))

        if i % 10 == 0:
            print('%i configs' % i + ' finished running')


def snoop_random(Strat, dataset, pair, runs, **kws):
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


from wmabollingerrsi import WMAForceBollingerRSIStrat
from wmamacdrsi import WMAMACDRSIStrat
from wmarsiobc import WMARSIOBCStrat

#import matplotlib.pyplot as plt


def demoRSIOBC(dataset, pair):
    port = Portfolio(10000)
    exchange = PaperExchange(commission=0.0012, slippage=0)
    strat = WMARSIOBCStrat(
            period=120,
            bband=6.0,
            bband_period=20,
            timelag_required=0,
            pair=pair,
            portfolio=port,
            exchange=exchange,
            equity_at_risk=1.0)

    test = Backtest(exchange)
    test.readJSON(dataset)
    test.run(strat)

    plotCandles(
            strat.bar,
            title='Final equity: {} Trades: {}'.format(port.equity, len(strat.trades)),
            trades=strat.trades)


def demoRSIStrat(dataset, pair):
    port = Portfolio(10000)
    exchange = PaperExchange(0.0012)
    strat = WMAForceBollingerRSIStrat(pair=pair, portfolio=port, exchange=exchange)

    test = Backtest(exchange)
    test.readJSON(dataset)
    test.run(strat)

    plotCandles(strat.bar)


def demoMACDStrat(dataset, pair):
    equity = []
    bband  = []

    def record_indicators(strat, equity, bband):
        equity.append((strat.last_timestamp, strat.equity))
        if len(strat.bar) > strat.bollinger.lookback:
            bband.append((strat.last_timestamp, strat.bollinger.band))

    port = Portfolio(10000)
    exchange = PaperExchange(commission=0.0012)
    strat = WMAMACDRSIStrat(
            period=120,
            timeframe=3600,
            bband=6.0,
            bband_period=20,
            pair=pair,
            portfolio=port,
            exchange=exchange,
            equity_at_risk=1.0)

    backtest_tick(
            strat,
            dataset,
            exchange=exchange,
            callback=lambda x: record_indicators(x, equity, bband))

    logger.report('MACD Equity:    %.2f' % port.equity)
    logger.report('MACD Cash:    %.2f' % port.cash)
    logger.report('MACD Asset:    %s' % str(port.balance))
    logger.report('Number of trades:  %d' % len(strat.trades))
    logger.report('Number of candles: %d' % len(strat.bar))

    equity = [[x[0] for x in equity], [x[1] for x in equity]]
    bband = [[x[0] for x in bband], [x[1] for x in bband]]

    plotCandles(
        strat.bar,
        title='Final equity: ${} Trades: {}'.format(strat.equity, len(strat.trades)),
        trades=strat.trades,
        indicators=[[bband], [equity]])


if __name__ == '__main__':
    snoop(WMAMACDRSIStrat, 'xrp.log', 'xrpusd')
    #demoMACDStrat('data/bch_correct.log',  'bchusd')
    #plt.show()

# This dummy stratagey is a naive implementation of the new version of strategy which leverages the
# Event bus architecture implemented by Pine
from cryptle.aggregator import Aggregator
from cryptle.registry   import Registry
from cryptle.event      import source, on
from cryptle.strategy   import SingleAssetStrat, OrderEventMixin

from metric.timeseries.bollinger  import BollingerBand
from metric.timeseries.candle     import CandleStick
from metric.timeseries.difference import Difference
from metric.timeseries.macd       import MACD
from metric.timeseries.rsi        import RSI
from metric.timeseries.wma        import WMA

import logging
logger = logging.getLogger('Strategy')

# requires linking from pine's work
class DummyStrat(SingleAssetStrat):

    def __init__(s,
        portfolio,
        message='New Era',
        bus    = None, # event bus passed into the DummyStrat
        pair   = 'btcusd',
        asset  = 'btc',
        period = 300,
        scope1 = 12,
        scope2 = 26,
        macd_scope = 9,
        bollinger_lb = 14,
        rsi_period = 12,
        rsi_thresh = 40,
        rsi_upperthresh = 70,
        **kws):

        SingleAssetStrat.__init__(s, asset)
        # Specify setup for local registry - @TODO
        setup = {'doneInit':   [s.doneInit, ['open'], [['once per bar'], {}], 1],
                 'wma':        [s.signifyWMA, ['open'], [['once per bar'], {'n per signal': ['doneInit', 10000]}], 2],
                 'singular':   [s.signifySingularity, ['open'], [['once per bar'], {'n per signal': ['doneInit', 10000]}], 3],
                 'rsi':        [s.signifyRSI, ['open'], [['once per bar'], {'n per signal': ['doneInit', 10000]}], 4],
                 'dlc':        [s.signifyDLC, ['open'], [['once per bar'], {'n per signal': ['doneInit', 10000]}], 5],
                 'enter':  [s.enter, ['open'], [['once per bar'], {'once per signal': ['dlc'], 'n per signal': ['doneInit', 10000]}], 6],
                 'exit':       [s.exit, ['open'], [['once per bar'], {'n per signal': ['doneInit', 10000]}], 7],
                 #'dido_scale': [s.dido_scale, ['open'], [['once per bar'], {'n per signal': ['doneInit', 10000]}], 8],
                }

        # Initiate candle aggregator and CandleStick
        s.bus          = bus
        s.portfolio    = portfolio
        s.registry     = Registry(setup, bus=s.bus)
        s.aggregator   = Aggregator(3600, bus=s.bus)
        s.stick        = CandleStick(3600, bus=s.bus)

        s.init_bar = max(scope1, scope2, macd_scope, rsi_period)
        s.message = message
        s.pair    = pair
        # Indicators
        s.wma1 = WMA(s.stick.o, scope1)
        s.wma2 = WMA(s.stick.o, scope2)
        s.macd = MACD(s.wma1, s.wma2, macd_scope)
        s.rsi  = RSI(s.stick.o, rsi_period)
        s.macd_value = Difference(s.macd)
        s.macd_diff  = Difference(s.macd.diff)
        s.rsi_diff = Difference(s.rsi)
        s.reaper   = BollingerBand(s.rsi_diff, s.rsi._lookback, sd=2)

        # Parameters
        s.rsi_upperthresh = rsi_upperthresh
        s.rsi_thresh      = rsi_thresh

        # Flags
        s.rsi_sell_flag = False
        s.rsi_signal = False

        # Trade-related flags
        s.sell_amount = None

    @source('signal')
    def emitSignal(s, signalName, boolean):
        return [signalName, boolean]

    @source('strategy:triggered')
    def emitTriggered(s, triggerName):
        return triggerName

    # at least it kinda works
    def doneInit(s):
        # check at every tick initially to see if s.registry.num_bars > s.init_bar
        # whenexec: after self.registry.num_bars > s.init_bars, triggerConstraint:[['open'],
        # [['once'], {}]]
        if s.registry.num_bars > s.init_bar:
            s.emitSignal('doneInit', True)
        else:
            print('doneInit checked', s.registry.num_bars, s.init_bar)


    def signifyWMA(s):
        try:
            #print('test successful')
            if (s.stick.o > s.wma1):
                s.emitSignal('wma', True)
            else:
                s.emitSignal('wma', False)
            s.emitTriggered('wma')
        except:
            pass

    # This function uses flags instead of signals1 - conventional way
    def signifyRSI(s):
        # only updates signal
        try:
            if s.rsi > s.rsi_upperthresh:
                s.rsi_sell_flag = True
                s.rsi_signal = True
            elif s.rsi > 50:
                s.rsi_signal = True

            if s.rsi_sell_flag and s.rsi < 50:
                s.rsi_signal = False
            if s.rsi < s.rsi_thresh:
                s.rsi_sell_flag = False
                s.rsi_signal = False
        except:
            pass

    def signifyDLC(s):
        try:
            if float(s.macd_value) > 0 and float(s.macd_diff) > 0:
                # emit signal for entry
                s.emitSignal('dlc', True)
            else:
                # emit signal for entry
                s.emitSignal('dlc', False)
            s.emitTriggered('dlc')
        except:
            pass

    ## issue on retrieving past Timeseries data
    #def signifyDIDO(s, data):
    #    # emit dlc signal
    #    someConditionToBeImplemented = True
    #    try:
    #        if someConditionToBeImplemented:
    #            s.emitSignal('dido', True)
    #            s.emitTriggered('dido')
    #        else:
    #            s.emitSignal('dido', False)
    #            s.emitTriggered('dido')
    #    except:
    #        pass

    def signifySingularity(s):
        try:
            if (s.rsi_diff > s.reaper.upperband):
                s.emitSignal('singular', False)
                s.emitTriggered('singular')
            else:
                s.emitSignal('singular', True)
                s.emitTriggered('singular')
        except:
            pass

    def enter(s):
    # execute only when RSI, DLC signal returns True and not screened
        print(s.hasCash, s.hasBalance)
        if s.hasCash and not s.hasBalance and s.rsi_signal:
            print('buying?', s.maxBuyAmount(s.registry.current_price), s.registry.num_bars)
            s.buy(s.maxBuyAmount(s.registry.current_price))
            s.sell_amount = s.maxSellAmount * 0.3
            print('Sell amount: {}'.format(s.sell_amount))
            s.emitTriggered('enter')
        print(s.maxBuyAmount(s.registry.current_price))

    def buy(s):
        print(s.registry.num_bars)
        s.bought = True

    def sell(s)L
        print(s.registry.num_bars)
        s.sold = True


    def exit(s):
    # execute via normal rsi exits
        if not s.rsi_signal and s.hasBalance:
            print('selling?', s.registry.num_bars)
            s.marketSell(s.maxSellAmount)
            s.emitTriggered('exit')

    #def dido_scale(s):
    ## execute scale off, max 3 + 1 times per trade, 30% each time
    #    if s.maxSellAmount > s.sell_amount:
    #        s.marketScaleOut(s.sell_amount)
    #    else:
    #        s.marketScaleOut(s.maxSellAmount * 0.999)
    #    s.emitTriggered('dido_scale')

    #def singular_scale(s):
    ## execute singular scale off, max 3 + 1 times per trade, 30% each time
    #    if s.maxSellAmount > s.sell_amount:
    #        s.marketScaleOut(s.sell_amount)
    #    else:
    #        s.marketScaleOut(s.maxSellAmount * 0.999)
    #    s.emitTriggered('singular_scale')

if __name__ == '__main__':
    from cryptle.backtest import backtest_tick, Backtest
    from cryptle.exchange.paper import Paper
    from cryptle.strategy import Portfolio
    from cryptle.plotting import *
    from cryptle.event import source, on, Bus
    from cryptle.logging import *

    fh = logging.FileHandler('dummy.log', mode='w')
    fh.setLevel(logging.TICK)

    sh = logging.StreamHandler()
    sh.setLevel(logging.REPORT)

    logger.addHandler(sh)
    logger.addHandler(fh)
    logger.setLevel(logging.DEBUG)

    base_logger = logging.getLogger('cryptle.new_strategy')
    base_logger.setLevel(logging.DEBUG)
    base_logger.addHandler(fh)

    equity = [[], []]
    def record_indicators(strat):
        global equity
        try:
            equity[0].append(strat.aggregator.last_bar_timestamp)
            equity[1].append(strat.adjusted_equity)
        except:
            pass

    dataset = 'btc01.log'

    pair = 'btcusd'
    asset = 'btc'
    base_currency = 'usd'
    port = Portfolio(cash=10000, base_currency=base_currency)
    exchange = Paper(0, commission=0.0013, slippage=0)
    bus = Bus()

    strat = DummyStrat(port, asset=asset, exchange=exchange, bus=bus, pair=pair)
    bus.bind(strat)
    #for i, item in bus._callbacks.items():
    #    print(i, item)
    backtest_tick(strat, dataset, bus=bus, pair=pair, portfolio=port, exchange=exchange, callback=record_indicators)

    logger.report('Equity:  %.2f' % port.equity({'btc': strat.registry.current_price}))
    logger.report('Cash:    %.2f' % port.cash)
    logger.report('Asset:   %s' % str(port.balance))
    logger.report('No. of trades;   %d' % len(strat.trades))
    logger.report('No. of candles:  %d' % strat.registry.num_bars)

    plot(
        strat.aggregator,
        title='Final equity: ${} Trades: {}'.format(strat.equity, len(strat.trades)),
        trades=strat.trades,
        indicators=[[equity]])

    plot.show()


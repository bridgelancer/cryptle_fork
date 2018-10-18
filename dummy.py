# This dummy stratagey is a naive implementation of the new version of strategy which leverages the
# Event bus architecture implemented by Pine
from cryptle.aggregator import Aggregator
from cryptle.registry   import Registry
from cryptle.event      import source, on
from cryptle.strategy   import Strategy, NewStrategy

from metric.timeseries.bollinger  import BollingerBand
from metric.timeseries.candle     import CandleStick
from metric.timeseries.difference import Difference
from metric.timeseries.macd       import MACD
from metric.timeseries.rsi        import RSI
from metric.timeseries.wma        import WMA

import logging
logger = logging.getLogger('Strategy')

# requires linking from pine's work
class DummyStrat(NewStrategy):

    def __init__(s,
        message='New Era',
        period = 300,
        scope1 = 12,
        scope2 = 26,
        macd_scope = 9,
        bollinger_lb = 14,
        rsi_period = 12,
        rsi_thresh = 40,
        rsi_upperthresh = 70,
        timelag = 10,
        **kws):

        s.message = message
        s.init_bar = max(scope1, scope2, macd_scope, rsi_period)
        super().__init__(**kws)
        # Specify setup for local registry - @TODO
        setup = {'doneInit':    [['open'], [['once per bar'], {}], 1],
                 #'belowRSIthresh':  [['open'], [['once per bar'], {'n per signal': ['doneInit', 10000]}, 2]],
                 'wma':         [['open'], [['once per bar'], {'n per signal': ['doneInit', 10000]}], 2]
                }

        # Initiate candle aggregator and CandleStick
        s.registry     = Registry(setup, bus=s.bus)
        s.aggregator   = Aggregator(3600, bus=s.bus)
        s.stick        = CandleStick(3600, bus=s.bus)

        # Indicators
        s.wma1 = WMA(s.stick.o, scope1)
        s.wma2 = WMA(s.stick.o, scope2)
        s.macd = MACD(s.wma1, s.wma2, macd_scope)
        s.rsi  = RSI(s.stick.o, rsi_period)
        s.macd_value = Difference(s.macd)
        s.macd_diff  = Difference(s.macd.diff)
        s.rsi_diff = Difference(s.rsi)
        s.reaper   = BollingerBand(s.rsi_diff, s.rsi._lookback, sd=2)

    @source('signal')
    def emitSignal(s, signalName, boolean):
        return [signalName, boolean]

    @source('strategy:triggered')
    def emitTriggered(s, triggerName):
        return triggerName

    # at least it kinda works
    @on('registry:execute')
    def doneInit(s, data):
        # check at every tick initially to see if s.registry.num_bars > s.init_bar
        # whenexec: after self.registry.num_bars > s.init_bars, triggerConstraint:[['open'],
        # [['once'], {}]]
        if data[0] == 'doneInit':
            print('doneInit checked', s.registry.num_bars, s.init_bar)
            if s.registry.num_bars > s.init_bar:
                print('finished doneInit')
                s.emitSignal('doneInit', True)
                s.emitTriggered('doneInit')

    @on('registry:execute')
    def signifyWMA(s, data):
        if data[0] == 'wma':
            try:
                print(s.registry.logic_status['wma'])
                if float(s.wma1) < float(s.stick.o):
                    print(float(s.wma1), float(s.stick.o))
                    s.emitTriggered('wma')
                else:
                    print(float(s.wma1), float(s.stick.o))
                    s.emitTriggered('wma')
                print('finished wma')
            except:
                pass

    #@on('registry:execute')
    #def signifyDLC(s, data):
    #    if data[0] == 'dlc':
    #        # emit dlc signal
    #        try:
    #            if float(s.macd_val) > 0 and float(s.macd_diff) > 0:
    #                s.emitSignal('dlc', True)
    #                s.emitTriggered('dlc')
    #            else:
    #                s.emitSignal('dlc', False)
    #                s.emitTriggered('dlc')
    #        except:
    #            pass

    ## issue on retrieving past Timeseries data
    #@on('registry:execute')
    #def signifyDIDO(s, data):
    #    if data[0] == 'dido':
    #        # emit dlc signal
    #        someConditionToBeImplemented = True
    #        try:
    #            if someConditionToBeImplemented:
    #                s.emitSignal('dido', True)
    #                s.emitTriggered('dido')
    #            else:
    #                s.emitSignal('dido', False)
    #                s.emitTriggered('dido')
    #        except:
    #            pass

    #@on('registry:execute')
    #def signifySingularity(s, data):
    #    if data[0] == 'singular':
    #        try:
    #            if (s.rsi_diff > s.reaper.upperband):
    #                s.emitSignal('singular', True)
    #                s.emitTriggered('singular')
    #            else:
    #                s.emitSignal('singular', False)
    #                s.emitTriggered('singular')
    #        except:
    #            pass

    #@on('registry:execute')
    #def signifyRSISellFlag(s, data):
    #    # whenexec = 'open'; triggerConstraint: [['once'], {}]
    #    if data[0] == 'aboveRSISellFlag':
    #        try:
    #            if float(s.rsi) > s.rsi_upperthresh:
    #                s.emitSignal('aboveRSISellFlag', True)
    #                s.emitTriggered('aboveRSISellFlag')
    #        except:
    #            pass

    #@on('registry:execute')
    #def signifyRSIBelowThresh(s, data):
    #    # whenexec = 'open'; triggerConstraint: [['once'], {}]
    #    if data[0] == 'belowRSIthresh':
    #        try:
    #            if float(s.rsi) < s.rsi_thresh:
    #                s.emitSignal('belowRSIthresh', True)
    #                s.emitSignal('aboveRSISellFlag', False)
    #                s.emitTriggered('belowRSIthres')
    #            print('partailly fucking works')
    #        except:
    #            pass

    ## now trying to solve the issue of running at the first instance before doneInit is called
    #@on('registry:execute')
    #def signifyRSIAbove50(s, data):
    #    # whenexec = 'open'; triggerConstraint: [['once'], {}]
    #    if data[0] == 'aboveRSI50':
    #        try:
    #            someConditionToBeImplemented = True
    #            if float(s.rsi) > 50:
    #                s.emitSignal('aboveRSI50', True)
    #            elif float(s.rsi) > 40 and someConditionToBeImplemented:
    #                s.emitSignal('aboveRSI50', False)
    #                s.emitSignal('belowRSIthresh', False)
    #            elif float(s.rsi) < 40:
    #                s.emitSignal('aboveRSI50', False)
    #            s.emitTriggered('aboveRSI50')
    #        except:
    #            pass


    #@on('registry:execute')
    #def screenRSIDiff(s, data):
    #    if data[0] == 'rsi_diff':
    #        try:
    #            if float(s.rsi_diff) > float(s.reaper.upperband):
    #                s.emitSignal('singular', True)
    #                s.emitTriggered('singular')
    #            else:
    #                s.emitSignal('singular', False)
    #                s.emitTriggered('singular')
    #        except:
    #            pass

    #@on('registry:execute')
    #def marketBuy(s, data):
    #    # execute only when RSI, DLC signal returns True and not screened
    #    if data[0] == 'marketBuy':
    #        try:
    #            if s.hasCash and not s.hasBalance:
    #                s.marketBuy(s.maxBuyAmount)
    #                s.sell_amount = s.maxSellAmount * 0.3
    #                s.emitTriggered('marketBuy')
    #        except:
    #            pass

    #@on('registry:exectue')
    #def exit(s, data):
    #    # execute via normal rsi exits
    #    if data[0] == 'exit':
    #        s.marketSell(s.maxSellAmount)
    #        logger.signal('Sell: Exit')
    #        s.emitTriggered('exit')

    #@on('registry:execute')
    #def dido_scale(s, data):
    #    # execute scale off, max 3 + 1 times per trade, 30% each time
    #    if data[0] == 'dido_scale':
    #        if s.maxSellAmount > s.sell_amount:
    #            s.marketScaleOut(s.sell_amount)
    #        else:
    #            s.marketScaleOut(s.maxSellAmount * 0.999)
    #        s.emitTriggered('dido_scale')

    #@on('registry:execute')
    #def singular_scale(s, data):
    #    # execute singular scale off, max 3 + 1 times per trade, 30% each time
    #    if data[0] == 'singular_scale':
    #        if s.maxSellAmount > s.sell_amount:
    #            s.marketScaleOut(s.sell_amount)
    #        else:
    #            s.marketScaleOut(s.maxSellAmount * 0.999)
    #        s.emitTriggered('singular_scale')

if __name__ == '__main__':
    from cryptle.backtest import backtest_tick, Backtest, PaperExchange
    from cryptle.strategy import Portfolio
    from cryptle.plotting import *
    from cryptle.event import source, on, Bus
    from cryptle.loglevel import *

    formatter = defaultFormatter(notimestamp=True)
    fh = logging.FileHandler('dummy.log', mode='w')
    fh.setLevel(logging.TICK)
    fh.setFormatter(formatter)

    sh = logging.StreamHandler()
    sh.setLevel(logging.REPORT)
    sh.setFormatter(formatter)

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

    dataset = 'bch1.log'

    pair = 'bchusd'
    asset = 'usd'
    base_currency = 'BCHUSD'
    port = Portfolio(10000)
    exchange = PaperExchange(commission=0.0013, slippage=0)
    bus = Bus()

    strat = DummyStrat(portfolio=port, exchange=exchange, bus=bus, asset=asset,
            base_currency=base_currency, pair=pair)
    bus.bind(strat)
    #for i, item in bus._callbacks.items():
    #    print(i, item)
    backtest_tick(strat, dataset, bus=bus, pair=pair, portfolio=port, exchange=exchange, callback=record_indicators)

    logger.report('Equity:  %.2f' % port.equity)
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


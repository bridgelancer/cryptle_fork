# This dummy stratagey is a naive implementation of the new version of strategy which leverages the
# Event bus architecture implemented by Pine
from cryptle.aggregator import Aggregator
from cryptle.registry   import Registry
from cryptle.event      import source, on
from cryptle.strategy   import Strategy, NewStrategy

from metric.timeseries.___  import imported_func1


import logging
logger = logging.getLogger('Strategy')


class Skeleton_Strat(NewStrategy):

    def __init__(self,
        any_predefined_arg,
        **kws):

        super().__init__(**kws)


        setup = {'actionname1': [self.func1, ["one of the lookup_check"], [['one of the
            lookup_trigger (for bar)'], {'one of the lookup_trigger (for
            signal)': ['actionname_to_listen_for', max_iterations], ...}],
            order_of_execution], ...}


        # Initiate candle aggregator and CandleStick
        self.registry     = Registry(setup, bus=self.bus)
        self.aggregator   = Aggregator(bar_interval, bus=self.bus)
        self.stick        = CandleStick(bar_interval, bus=self.bus)


        # Indicators, used in making the requirements before emitting signals, see below
        self.indi1 = imported_func1(args)

        # Parameters, usually for using pre_defined_args directly before emitting
        self.para = para1


    @source('signal')
    def emitSignal(self, signalName, boolean):
        return [signalName, boolean]

    @source('strategy:triggered')
    def emitTriggered(self, triggerName):
        return triggerName

    def func1(self):

        if requirements_are_fulfiled:
            # emit signal with True will start the applying the constraints, i.e. the
            # limitation on number of times ran
            self.emitSignal('actionname1', True)

        else:
            # emit signal with False will block the client codes execution, needed because
            # of hardcoding restart of the signal
            self.emitSignal('actionname1', False)

        # executing the action with the following action name, the registry will check
        # whether all constraints are fulfiled
        self.emitTriggered('actionname1')


    def entry(self, data):

        if all_requirements_met:

            if self.hasCash and not self.hasBalance:

                self.marketBuy(self.maxBuyAmount)
                self.sell_amount = self.maxSellAmount * scale_off

                logger.signal()
                self.emitTriggered('marketBuy')


    def exit(self, data):

        if requirements_met:

            self.marketSell(self.maxSellAmount)

            logger.signal()
            self.emitTriggered('exit')


# Temporary
if __name__ == '__main__':
    from cryptle.backtest import backtest_tick, Backtest, PaperExchange
    from cryptle.strategy import Portfolio
    from cryptle.plotting import *
    from cryptle.event import source, on, Bus
    from cryptle.loglevel import *

    fh = logging.FileHandler('skt.log', mode='w')
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
    asset = 'usd'
    base_currency = 'BTCUSD'
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

from cryptle.strategy import Strategy
from cryptle.loglevel import *

from metric.candle import *
from metric.generic import *

import logging
logger = logging.getLogger('Strategy')

class DeltaStrat(Strategy):

    def __init__(s,
            message='The New Hope',
            period=300,
            scope1=12,
            scope2=26,
            macd_scope=9,
            rsi_period=12,
            rsi_thresh=40,
            rsi_upper_thresh=70,
            timelag=10,
            **kws):

        # Set meta info
        s.message = message

        # Initialize strategy parameters
        s.period = period
        s.timelag = timelag
        s.rsi_thresh = rsi_thresh
        s.rsi_upper_thresh = rsi_upper_thresh

        # Initialize metrics
        s.indicators = {}
        s.indicators['bar'] = bar = CandleBar(period)
        super().__init__(**kws)

        s.wma1 = WMA(bar, scope1)
        s.wma2 = WMA(bar, scope2)
        s.macd = MACD(s.wma1, s.wma2, macd_scope)
        s.rsi = RSI(bar, rsi_period)

        s.macddlc = Difference(s.macd, 'diff', 'diff_ma') # to be integrated

        # Initialize flags and states
        s.init_time = 0
        s.init_bar = max(scope1, scope2, macd_scope, rsi_period)
        s.dlc_signal = False
        s.rsi_signal = False
        s.rsi_sell_flag = False


    def handleTick(s, price, timestamp, volume, action):
        if not s.doneInit(timestamp):
            return -1

        s.signifyDLC()
        s.signifyRSI()

    # initation phase - return and do nothing before initiation is done
    def doneInit(s, timestamp):
        if s.init_time == 0:
            s.init_time = timestamp
        return timestamp > s.init_time + s.init_bar * s.bar.period

    # generate new DLC signal in place of the old MACD signal
    def signifyDLC(s):
        value = s.macddlc.value
        diff = s.macddlc.diff
        diff_ma = s.macddlc.diff_ma

        new_dlc_signal = value > 0 and diff > 0
        if new_dlc_signal and not s.dlc_signal:
            logger.metric('DLC: Double In')
        s.dlc_signal = new_dlc_signal

    # @Fix dodgy logic, though data snooping gives better return
    # RSI over 80 sell leads to 5% less return
    def signifyRSI(s):
        if s.rsi > s.rsi_upper_thresh:
            s.rsi_sell_flag = True
            s.rsi_signal = True
        elif s.rsi > s.rsi_thresh:
            s.rsi_signal = True

        # if rsi_sell_flag is up, we allow it to sell when rsi < 50
        if s.rsi_sell_flag and s.rsi < 50:
            s.rsi_signal = False
        if s.rsi < s.rsi_thresh:
            s.rsi_sell_flag = False
            s.rsi_signal = False


    def execute(s, timestamp):
        if s.hasCash and not s.hasBalance:
            if (
                    s.rsi_signal
                    and s.dlc_signal
               ):
                s.marketBuy(s.maxBuyAmount)
                s.reset_params()

        elif s.hasBalance:
            if not s.rsi_signal and s.rsi_sell_flag:
                s.marketSell(s.maxSellAmount)
                s.reset_params()
                logger.signal('Sell: Over 70 RSI')

            elif not s.rsi_signal and not s.dlc_signal:
                s.marketSell(s.maxSellAmount)
                s.reset_params()
                logger.signal('Sell: RSI + MACD')

    def reset_params(s):
        s.rsi_sell_flag = False

if __name__ == '__main__':
    from cryptle.backtest import backtest_tick, Backtest, PaperExchange
    from cryptle.strategy import Portfolio
    from cryptle.plotting import *

    formatter = defaultFormatter(notimestamp=True)

    fh = logging.FileHandler('snb.log', mode = 'w')
    fh.setLevel(logging.TICK)
    fh.setFormatter(formatter)

    sh = logging.StreamHandler()
    sh.setLevel(logging.REPORT)
    sh.setFormatter(formatter)

    logger.addHandler(sh)
    logger.addHandler(fh)
    logger.setLevel(logging.DEBUG)

    base_logger = logging.getLogger('cryptle.strategy')
    base_logger.setLevel(logging.DEBUG)
    base_logger.addHandler(fh)

    equity = [[], []]
    def record_indicators(strat):
        global equity
        equity[0].append(strat.last_timestamp)
        equity[1].append(strat.adjusted_equity)

    dataset = 'bch.log'

    pair = 'bchusd'
    port = Portfolio(10000)
    exchange = PaperExchange(commission=0.0012, slippage=0)

    backtest_tick(strat, dataset, exchange=exchange, callback=record_indicators)

    logger.report('Equity:  %.2f' % port.equity)
    logger.report('Cash:    %.2f' % port.cash)
    logger.report('Asset:    %s' % str(port.balance))
    logger.report('No. of trades:  %d' % len(strat.trades))
    logger.report('No. of candles:  %d' % len(strat.bar))

    plot(
        strat.bar,
        title='Final equity: ${} Trades: {}'.format(strat.equity, len(strat.trades)),
        trades=strat.trades,
        indicators=[[equity]])

    plt.show()
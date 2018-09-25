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
                s.buy_amount = s.maxBuyAmount
                s.marketBuy(s.maxBuyAmount)
                s.buy_price = price
                s.buy_time = timestamp
                s.was_stoploss = False
                s.reset_params()
            elif(
                    s.rsi_signal
                    and s.dlc_signal
                    and s.screened
                    and not s.hasBalance
                ):
                s.buy_amount = s.maxBuyAmount * 0.00000001
                s.marketBuy(s.maxBuyAmount*0.00000001)
                logger.signal('Screened')
                s.buy_price = price
                s.buy_time = timestamp
                s.was_stoploss = False
                s.reset_params()

        elif s.hasBalance:
            if not s.rsi_signal and s.rsi_sell_flag:
                s.marketSell(s.maxSellAmount)
                s.reset_params()
                logger.signal('Sell: Over 70 RSI')

            elif not s.rsi_signal and not s.dlc_signal:
                s.marketSell(s.maxSellAmount)
                s.reset_params()
                logger.metric('Percent gain: {}'.format((price/s.buy_price -1) * 100))
                logger.signal('Sell: RSI')
                s.buy_price = None
                s.buy_time = None
                s.buy_amount = None

            if s.trailing_stop and not s.was_triggered:
                print("Trigger time: {}".format(datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')))
                print("BOLLINGER: buy: {}, current:{}, stoploss: {}".format(s.buy_price, price,
                    s.stoploss_level))
                try:
                    s.marketSell(float(s.buy_amount * 0.3))
                    logger.metric('Percent gain: {}'.format((price/s.buy_price -1) * 100))
                except Exception as e:
                    print(e)
                    s.marketSell(s.maxSellAmount * 0.999)
                    logger.metric('Percent gain: {}'.format((price/s.buy_price -1) * 100))
                logger.signal('Sell: Bollinger trailing stop')

                s.prev_triggered_time = s.triggered_time
                s.was_triggered = True
                s.triggered_time = None
                s.triggered_current = None
                s.stoploss_level = None
            #if s.dido and not s.was_dido:
                #s.marketSell(s.maxSellAmount * 0.5)
                #logger.signal('Scale off: DIDO')
                ## need to flag this
                #s.was_dido = True
                #s.dido_time = timestamp

            # scaling off after 1% gain to recover commission, only execute once per trade
            #if s.hasBalance and s.margin and not s.was1p:
                #s.marketSell(s.maxSellAmount * 0.999)
                #logger.signal('Scale off: commission recovered')
                #s.was1p = True

            # stop loss if the position is down by 2%
            #if s.hasBalance and s.stoploss and not s.was_stoploss:
                #s.marketSell(s.maxSellAmount * 0.999)
                #logger.signal('Stop loss')
                #s.was_stoploss = True
                #s.reset_params()

            #if s.hasBalance and s.singular and not s.was_singular:
            #    s.marketSell(s.maxSellAmount * 0.5)
            #    logger.signal('Benefit Reaped')
            #    s.was_singular = True

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

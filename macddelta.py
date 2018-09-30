from cryptle.strategy import Strategy
from cryptle.loglevel import *

from metric.candle import *
from metric.generic import *

import logging
import json
from datetime import date
logger = logging.getLogger('Strategy')

class DeltaStrat(Strategy):

    def __init__(s,
            message='The New Hope',
            period=1800,
            scope1=12,
            scope2=26,
            macd_scope=9,
            rsi_period=14,
            rsi_thresh=39,
            rsi_upper_thresh=71,
            bollinger_lb=14,
            **kws):

        # Set meta info
        s.message = message

        # Initialize strategy parameters
        s.period = period
        s.rsi_thresh = rsi_thresh
        s.rsi_upper_thresh = rsi_upper_thresh

        # Initialize metrics
        s.indicators = {}
        s.indicators['bar'] = bar = CandleBar(period)
        super().__init__(**kws)

        s.wma1 = WMA(bar, scope1)
        s.wma2 = WMA(bar, scope2)
        s.bollinger = BollingerBand(bar, bollinger_lb, sd=3)
        s.bollinger_stoploss = BollingerBand(bar, bollinger_lb, sd=2.5)
        s.macd = MACD(s.wma1, s.wma2, macd_scope)
        s.rsi = RSI(bar, rsi_period)

        s.macddlc = Difference(s.macd, 'diff', 'diff_ma')
        s.rsi_diff = Difference(s.rsi)
        s.reaper = BollingerBand(s.rsi_diff, s.rsi._lookback, sd=2, use_zero=True)

        # Initialize flags and states
        s.init_time = 0
        s.init_bar = max(scope1, scope2, macd_scope, rsi_period)

        s.buy_price = None
        s.buy_amount = None
        s.buy_time = None

        s.dlc_signal = False
        s.rsi_signal = False
        s.rsi_sell_flag = False

        s.dido = False
        s.was_dido = False
        s.dido_time = None

        s.margin = False
        s.was1p = False

        s.stoploss = False
        s.was_stoploss = False

        s.singular = False
        s.was_singular = False

        s.current = None
        s.triggered_current = None
        s.triggered_time = None
        s.prev_triggered_time = s.buy_time
        s.stoploss_level = None

        s.trailing_stop = False
        s.screened = False
        s.was_triggered = False
        s.sell_amount = None

    def handleTick(s, price, timestamp, volume, action):
        if not s.doneInit(timestamp):
            return -1

        s.signifyTrailingStop(price, timestamp)
        s.signifyDLC()
        s.signifyRSI()
        #s.signifyDIDO(timestamp)
        #s.signifyScaleOff(price)
        #s.signifyStopLoss(price)
        #s.signifySingularity(timestamp)
        s.screenRSIDiff()
        s.predictModel()
        s.logTrade(price, timestamp, volume, action)

# initation phase - return and do nothing before initiation is done
    def doneInit(s, timestamp):
        if s.init_time == 0:
            s.init_time = timestamp
        return timestamp > s.init_time + s.init_bar * s.bar.period

    # this places a intrabar trailling stop that is 0.5 sd below the current bar high whenever the
    # current price exceeds the 3.0 sd of the 14 day SMA value
    def signifyTrailingStop(s, price, timestamp):
        if s.hasBalance:
            s.trigger_level = float(s.bollinger.upperband)
            #logger.metric("timestamp: {}, price: {}, high: {}, stoploss:{}".format(timestamp, price, s.bar.last_high, s.stoploss_level))
            if ((price > s.trigger_level) and
                    ((s.prev_triggered_time is not None and s.triggered_time is None) or
                        (s.prev_triggered_time is None and s.triggered_time is None))):
                try:
                    if (timestamp - s.prev_triggered_time) //s.period > 0:
                        s.was_triggered = False
                        s.triggered_time = timestamp
                        s.triggered_current = 0
                except:
                    if (timestamp - s.buy_time) // s.period > 0:
                        s.was_triggered = False
                        s.triggered_time = timestamp
                        s.triggered_current = 0
            # update stoploss level if the trailling stoploss is triggered
            if s.triggered_time is not None:
                s.stoploss_level = float(s.bar.last_high - (float(s.bollinger.upperband) - float(s.bollinger_stoploss.upperband)))

            if not s.was_triggered and s.triggered_time is not None and (timestamp - s.triggered_time) // s.period >= s.triggered_current:
                #logger.metric("time:{}, upperband:{}, stoploss:{}".format(datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S'), float(s.trigger_level), s.stoploss_level))
                s.triggered_current += 1

            try:
                if price < s.stoploss_level:
                    s.trailing_stop = True
                else:
                    s.trailing_stop = False
            except:
                pass

    def signifyDLC(s):
        value = s.macddlc.value
        diff = s.macddlc.diff
        diff_ma = s.macddlc.diff_ma

        new_dlc_signal = value > 0 and diff > 0
        s.dlc_signal = new_dlc_signal

    def signifyDIDO(s, timestamp):
        dido = s.macddlc.output # the dictionary held by macddlc

        if s.dido_time is not None:
            if timestamp > s.dido_time + s.bar.period:
                s.was_dido = False
                s.dido_time = None

        if all(x < 0 for x in dido['value'][:2]) and all (x > 0 for x in dido['value'][2:]) and \
            all(x < 0 for x in dido['diff'][:2]) and all (x > 0 for x in dido['diff'][2:]):
            new_dido = True
        else:
            new_dido = False
        s.dido = new_dido

#    # use buy price and current price to determine the scale off
#    def signifyScaleOff(s, price):
#        if s.was1p:
#            return
#        margin = 1.01

#        if s.buy_price is not None:
#            if price > s.buy_price * margin: s.margin = True
#            else: s.margin = False

#    # set hard stop level level
#    def signifyStopLoss(s, price):
#        loss = 0.02
#        if s.buy_price is not None:
#            if price < s.buy_price * (1- loss): s.stoploss = True
#            else: s.stoploss = False

    # implement RSI-DLC bollinger scaling off, not running for the first bar
    def signifySingularity(s, timestamp):
        if s.was_singular:
            return

        if s.buy_time is not None:
            if (        s.rsi_diff > s.reaper.upperband \
                and timestamp > s.buy_time + s.bar.period):
                s.singular = True
            else:
                s.singular = False
        else:
            s.singular = False

    def signifyRSI(s):
        if s.rsi > s.rsi_upper_thresh:
            s.rsi_sell_flag = True
            s.rsi_signal = True
        elif s.rsi > 50:
            s.rsi_signal = True

        # if rsi_sell_flag is up, we allow it to sell when rsi < 50
        if s.rsi_sell_flag and s.rsi < 50:
            s.rsi_signal = False
        if s.rsi < s.rsi_thresh:
            s.rsi_sell_flag = False
            s.rsi_signal = False

    # Prohibit entry of position when difference of RSI exceedes its bollingerband
    def screenRSIDiff(s):
        if s.rsi_diff > s.reaper.upperband:
            s.screened = True
        else:
            s.screened = False


    # perform data collection and model training, perform prediction afterwards
    def predictModel(s):
        pass

    def logTrade(s, price, timestamp, volume, action):
        if s.hasBalance:
            if s.current is None:
                s.current = 0

            if (timestamp - s.buy_time) // s.period > s.current: # take the bar preceding the latest one
                logger.metric(json.dumps({"Open price": s.bar.open_prices(2)[0],  "Close price":
                    s.bar.close_prices(2)[0], "High price": s.bar.high_prices(2)[0], "Low price":
                    s.bar.low_prices(2)[0]}))
                s.current += 1

    def execute(s, timestamp, price):
        if s.hasCash and not s.hasBalance:
            if (
                    s.rsi_signal
                    and s.dlc_signal
                    and not s.screened
               ):
                s.marketBuy(s.maxBuyAmount)
                s.sell_amount = s.maxSellAmount * 0.3
                s.buy_price = price
                s.buy_amount = s.maxBuyAmount
                s.buy_time = timestamp
                s.was_stoploss = False
                logger.metric(json.dumps({"Buy Price": s.buy_price}))
                s.reset_params()
            elif(
                    s.rsi_signal
                    and s.dlc_signal
                    and s.screened
                    and not s.hasBalance
                ):
                logger.signal('Screened')
                s.marketBuy(s.maxBuyAmount*1e-100)
                s.sell_amount = s.maxSellAmount * 0.3
                s.buy_price = price
                s.buy_time = timestamp
                s.was_stoploss = False
                logger.metric(json.dumps({"Buy Price": s.buy_price}))
                s.reset_params()

        elif s.hasBalance:
            if not s.rsi_signal and s.rsi_sell_flag:
                s.marketSell(s.maxSellAmount)
                s.reset_params()
                logger.metric(json.dumps({'Percent gain': (price/s.buy_price - 1) * 100}))
                logger.signal('Sell: Over 70 RSI')
                s.buy_price = None
                s.buy_time = None
                s.buy_amount = None
                s.sell_amount = None

            elif not s.rsi_signal:
                s.marketSell(s.maxSellAmount)
                s.reset_params()
                logger.metric(json.dumps({'Percent gain': (price/s.buy_price - 1) * 100}))
                logger.signal('Sell: RSI')
                s.buy_price = None
                s.buy_time = None
                s.buy_amount = None
                s.sell_amount = None

#            if s.trailing_stop and not s.was_triggered:
#                print("Trigger time: {}".format(datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')))
#                print("BOLLINGER: buy: {}, current:{}, stoploss: {}".format(s.buy_price, price,
#                    s.stoploss_level))
#                if s.maxSellAmount > s.sell_amount:
#                    s.marketSell(s.sell_amount)
#                    #s.sell_amount *= 2
#                    logger.metric('Percent gain: {}'.format((price/s.buy_price -1) * 100))
#                else:
#                    s.marketSell(s.maxSellAmount * 0.999)
#                    logger.metric('Percent gain: {}'.format((price/s.buy_price -1) * 100))
#                logger.signal('Sell: Bollinger trailing stop')
#
#                s.prev_triggered_time = s.triggered_time
#                s.was_triggered = True
#                s.triggered_time = None
#                s.triggered_current = None
#                s.stoploss_level = None

            if s.dido and not s.was_dido:
                logger.signal('Scale off: DIDO')
                if s.maxSellAmount > s.sell_amount:
                    s.marketSell(s.sell_amount)
                    logger.metric(json.dumps({'Percent gain': (price/s.buy_price - 1) * 100}))
                else:
                    s.marketSell(s.maxSellAmount * 0.999)
                    logger.metric(json.dumps({'Percent gain': (price/s.buy_price - 1) * 100}))
                # need to flag this
                s.was_dido = True
                s.dido_time = timestamp

            ## scaling off after 1% gain to recover commission, only execute once per trade
            #if s.hasBalance and s.margin and not s.was1p:
            #   s.marketSell(s.maxSellAmount * 0.999)
            #   logger.signal('Scale off: commission recovered')
            #   s.was1p = True

            ## stop loss if the position is down by 2%
            #if s.hasBalance and s.stoploss and not s.was_stoploss:
            #   s.marketSell(s.maxSellAmount * 0.999)
            #   logger.signal('Stop loss')
            #   s.was_stoploss = True
            #   s.reset_params()

            if s.hasBalance and s.singular and not s.was_singular:
                logger.signal('Benefit Reaped')
                if s.maxSellAmount > s.sell_amount:
                    s.marketSell(s.sell_amount)
                    logger.metric(json.dumps({'Percent gain': (price/s.buy_price - 1) * 100}))
                else:
                    s.marketSell(s.maxSellAmount * 0.999)
                    logger.metric(json.dumps({'Percent gain': (price/s.buy_price - 1) * 100}))
                s.was_singular = True

    def reset_params(s):
        s.rsi_sell_flag = False
        s.was1p = False
        s.was_singular = False
        s.stoploss = False
        s.current = None

        s.was_triggered = False
        s.triggered_current = None
        s.triggered_time = None
        s.trailing_stop = False

if __name__ == '__main__':
    from cryptle.backtest import backtest_tick, Backtest, PaperExchange
    from cryptle.strategy import Portfolio
    from cryptle.plotting import *

    formatter = defaultFormatter(notimestamp=True)
    fh = logging.FileHandler('log/xaf.log', mode = 'w')
    fh.setLevel(logging.DEBUG)
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

    dataset = 'log/xaf'

    port = Portfolio(10000)
    exchange = PaperExchange(commission=0.0013, slippage=0)

    strat = DeltaStrat(message = '[DLC]', portfolio=port, exchange=exchange, asset="USD",
            base_currency="BTCUSD",)

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

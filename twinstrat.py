from cryptle.strategy import Strategy, IntensityFlag
from cryptle.loglevel import *
from cryptle.utility  import *
from ta import *

import logging
logger = logging.getLogger('Cryptle')


class TwinStrat(Strategy):

    def __init__(s,
            period=120,
            bband=8.0,
            boll_lb=20,
            boll_tradable_len=3600,
            uatr=0.5,
            latr=0.5,
            ma1_lb=5,
            ma2_lb=8,
            macd_lb=5,
            rsi_lb=14,
            stoploss_percent=1,
            stoploss_cooldown=120,
            message='[Twin]',
            **kws):

        s.indicators = {}
        s.indicators['bar'] = CandleBar(period)

        super().__init__(**kws)

        s.atr = ATR(s.bar, ma1_lb)
        s.wma1 = WMA(s.bar, ma1_lb)
        s.wma2 = WMA(s.bar, ma2_lb)
        s.macd = MACD_WMA(s.wma1, s.wma2, macd_lb)
        s.sma = SMA(s.bar, boll_lb)
        s.bollinger = BollingerBand(s.sma, boll_lb)
        s.rsi = RSI(s.bar, rsi_lb)

        s.period = period
        s.message = message
        s.uatr = uatr
        s.latr = latr
        s.bband = bband
        s.boll_tradable_len = boll_tradable_len
        s.stoploss_percent = stoploss_percent
        s.stoploss_cooldown = stoploss_cooldown

        s.prev_buy_price = 0
        s.prev_buy_time = 0
        s.prev_sell_time = 0
        s.tradable_window = 0
        s.init_time = 0
        s.bought_at_uptrend = False
        s.stoploss_flag = False
        s.was_stoploss = False

        s.atr_signal = False
        s.macd_signal = False
        s.rsi_sell_flag = False
        s.rsi_flag = IntensityFlag()
        s.bollinger_flag = IntensityFlag()


    def handleTick(s, price, timestamp, volume, action):
        if not s.doneInit(timestamp):
            return -1

        s.signifyATR(price)
        s.signifyBoll(timestamp)
        s.signifyMACD()
        s.signifyRSI()
        s.signifyStoploss(price)

        # Prevent trade if the tick was within the same bar
        if int(timestamp / s.period) == int(s.prev_buy_time / s.period):
            return -1


    def doneInit(s, timestamp):
        if s.init_time == 0:
            s.init_time = timestamp
        return timestamp > s.init_time + max(s.wma1.lookback, 10) * s.bar.period


    def signifyATR(s, price):
        s.atr_signal = False
        atr = s.atr.atr

        belowatr = max(s.wma1.wma, s.wma2.wma) < price - s.latr * atr
        aboveatr = min(s.wma1.wma, s.wma2.wma) > price + s.uatr * atr
        s.uptrend   = s.wma1.wma > s.wma2.wma
        s.downtrend = s.wma1.wma < s.wma2.wma

        if belowatr:
            s.atr_signal = True
        elif not s.bought_at_uptrend and aboveatr:
            s.atr_signal = False
        elif s.bought_at_uptrend and s.downtrend:
            s.atr_signal = False
        elif not s.bought_at_uptrend and  s.uptrend:
            s.bought_at_uptrend = True


    def signifyBoll(s, timestamp):
        if s.bollinger > s.bband:
            s.bollinger_flag.setHigh()
            s.tradable_window = timestamp

        if timestamp > s.tradable_window + s.boll_tradable_len:
            s.bollinger_flag.setLow()


    def signifyMACD(s):
        if s.macd.diff_ma < s.macd.diff:
            s.macd_signal = True
        else:
            s.macd_signal = False


    def signifyRSI(s):
        if s.rsi.rsi > 50:
            s.rsi_flag.setHigh()

        if s.rsi.rsi > 70:
            s.rsi_sell_flag = True

        if s.rsi_sell_flag and s.downtrend:
            s.rsi_flag.setLow()

        if s.rsi.rsi < 50:
            s.rsi_flag .setLow()
            s.rsi_sell_flag = False


    def signifyStoploss(s, price):
        if price <= s.prev_buy_price * (100 - s.stoploss_percent) / 100:
            s.stoploss_flag = True


    def execute(s, timestamp):
        if s.hasCash and not s.hasBalance:
            if s.was_stoploss and timestamp < s.stoploss_cooldown + s.prev_sell_time:
                return

            if s.rsi_flag.high and s.bollinger_flag.high and s.macd_signal:
                s.marketBuy(s.maxBuyAmount)
                s.prev_buy_time = timestamp
                s.prev_buy_price = s.last_price
                s.bought_at_uptrend = s.uptrend
                s.bought_at_reversion = False
                s.was_stoploss = False
            elif s.rsi_flag.low and s.bollinger_flag.low and s.atr_signal:
                s.marketBuy(s.maxBuyAmount)
                s.prev_buy_time = timestamp
                s.bought_at_uptrend = s.uptrend
                s.bought_at_reversion = True

        elif s.hasBalance:
            if s.stoploss_flag:
                s.marketSell(s.maxSellAmount)
                s.was_stoploss = True
                s.prev_sell_time = timestamp
            elif s.rsi_flag.low and not s.bought_at_reversion:
                s.marketSell(s.maxSellAmount)
                s.prev_sell_time = timestamp
            elif s.bought_at_reversion and s.rsi_flag.high and not s.atr_signal:
                s.marketSell(s.maxSellAmount)


if __name__ == '__main__':
    from cryptle.backtest import backtest_tick, Backtest, PaperExchange
    from cryptle.strategy import Portfolio
    from cryptle.plotting import *
    import matplotlib.pyplot as plt

    formatter = defaultFormatter()
    fh = logging.FileHandler('twinstrat.log', mode='w')
    fh.setLevel(logging.METRIC)
    fh.setFormatter(formatter)
    sh = logging.StreamHandler()
    sh.setLevel(logging.REPORT)
    sh.setFormatter(formatter)
    logger.setLevel(logging.METRIC)
    logger.addHandler(sh)
    logger.addHandler(fh)

    equity = []

    def record_indicators(strat):
        global equity
        equity.append((strat.last_timestamp, strat.equity))

    dataset = 'bch_correct.log'

    pair = 'bchusd'
    port = Portfolio(10000)
    exchange = PaperExchange(commission=0.0012, slippage=0)

    strat = TwinStrat(
            period=120,
            bband=8.0,
            boll_lb=20,
            boll_tradable_len=3600,
            pair=pair,
            portfolio=port,
            exchange=exchange,
            equity_at_risk=1.0)

    backtest_tick(strat, dataset, exchange=exchange, callback=record_indicators)

    logger.report('Twin Equity:    %.2f' % port.equity)
    logger.report('Twin Cash:    %.2f' % port.cash)
    logger.report('Twin Asset:    %s' % str(port.balance))
    logger.report('Number of trades:  %d' % len(strat.trades))
    logger.report('Number of candles: %d' % len(strat.bar))

    equity = [[x[0] for x in equity], [x[1] for x in equity]]
    plot(
        strat.bar,
        title='Final equity: ${} Trades: {}'.format(strat.equity, len(strat.trades)),
        trades=strat.trades,
        indicators=[[equity]])
    plt.show()

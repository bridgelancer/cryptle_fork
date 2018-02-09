from cryptle.strategy import Strategy
from cryptle.loglevel import *
from cryptle.utility  import *
from metric.candle import *
from metric.generic import *

import logging
logger = logging.getLogger('Strategy')

class SNBStrat(Strategy):

    def __init__(s,
            message='',
            period=120,
            scope1=5,
            scope2=8,
            macd_scope=4,
            bband=6.0,
            bband_period=20,
            boll_window=3600,
            snb_period=10,
            snb_factor=1.25,
            rsi_period=14,
            upper_atr=0.5,
            lower_atr=0.5,
            **kws)

        # Set meta info
        s.message = message

        # Initialize strategy parameters
        s.period = period
        s.upper_atr = upper_atr
        s.lower_atr = lower_atr
        s.boll_window = boll_window
        s.bband = bband
        s.snb_factor = snb_factor

        # Initialize metrics
        s.indicators = {}
        s.indicators['bar'] = bar = CandleBar(period)
        super().__init__(**kws)

        s.atr = ATR(bar, scope1)
        s.wma1 = WMA(bar, scope1)
        s.wma2 = WMA(bar, scope2)
        s.macd = MACD(bar, scope1, scope2, macd_scope)
        s.boll = BollingerBand(bar, bband_period, roll_method=simple_moving_average)
        s.snb = MANB(s.boll, snb_period, roll_method=simple_moving_average)
        s.rsi = RSI(bar, rsi_period)

        # Initialize flags and states
        s.init_time = 0
        s.tradable_window = 0
        s.bollinger_signal = False
        s.rsi_sell_flag = False
        s.rsi_sell_flag_80 = False
        s.rsi_signal = None
        s.prev_crossover_time = None


    def handleTick(s, price, ts, volume, action):
        if not s.doneInit(ts):
            return -1

        s.signifyATR(price)
        s.signifyBoll(timestamp)
        s.signifyMACD()
        s.signifyRSI()


    def doneInit(s, ts):
        if s.init_time == 0:
            s.init_time = ts
        return ts > s.init_time + max(s.wma1.lookback, 20) * s.bar.period


    def signifyATR(s, price):
        belowatr = max(s.wma1, s.wma2) < price - s.latr * atr
        s.downtrend = s.wma1.wma < s.wma2.wma

        if not belowatr:
            s.prev_crossover_time = None


    def signifyBoll(s, timestamp):
        if s.bollinger > s.bband:
            if not s.bollinger_signal:
                logger.signal('Bollinger window opened')
            s.bollinger_signal = True
            s.tradable_window = timestamp
        elif s.snb.sma[-1] * s.sna_factor < s.bollinger.band and s.bollinger.band > 6:
            if not s.bollinger_signal:
                logger.signal('Bollinger window opened with snb')
            s.bollinger_signal = True
            s.tradable_window = timestamp
        elif timestamp > s.tradable_window + s.boll_window:
            logger.signal('Bollinger window closed')
            s.bollinger_signal = False


    def signifyMACD(s):
        s.macd_signal = s.macd < 0


    def signifyRSI(s):
        if s.rsi > 50:
            s.rsi_signal = True

        if s.rsi > 70:
            s.rsi_sell_flag = True
            logger.signal('RSI over 70')

        if s.rsi > 80:
            s.rsi_sell_flag_80 = True
            logger.signal('RSI over 80')

        if s8rsi_sell_flag_80 and s.rsi < 70:
            s.rsi_signal = False
            logger.signal('RSI dropped from 80 to 70')

        if s.rsi_sell_flag and s.downtrend:
            s.rsi_signal = False

        if s.rsi.rsi < 50:
            s.rsi_signal = False


    def execute(s, ts):
        if s.hasCash and not s.hasBalance and s.rsi_signal and s.bollinger_signal and s.macd_signal:
            if s.prev_crossover_time is None:
                s.prev_crossover_time = timestamp # @Hardcode @Fix logic, do not use timestamp here

            elif timestamp - s.prev_crossover_time >= s.timelag_required:
                s.marketBuy(s.maxBuyAmount)
                s.reset_params()

        elif s.hasBalance and s.rsi_ssignal and s.rsi_sell_flag:
            s.marketSell(s.maxSellAmount)
            s.reset_params()
            logger.signal('Sell: Over 70 RSI')

        elif s.hasBalance and s.rsi_ssignal and s.rsi_sell_flag_80:
            s.marketSell(s.maxSellAmount)
            s.reset_params()
            logger.signal('Sell: Over 80 RSI')

        elif s.hasBalance and s.rsi_ssignal and not s.macd_signal:
            s.marketSell(s.maxSellAmount)
            s.reset_params()
            logger.signal('Sell: RSI + MACD')


    def reset_params(s):
        s.prev_crossover_time = None
        s.rsi_sell_flag = False
        s.rsi_sell_flag_80 = False

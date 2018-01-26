from ta import *
from cryptle.backtest import PaperExchange
from cryptle.strategy import *
from cryptle.loglevel import *
from cryptle.utility  import *

from datetime import datetime
import json
import logging


logger = logging.getLogger('Cryptle')


# @DEPRECATED
class OldStrat(Strategy):

    def __init__(self, pair, portfolio):
        super().__init__(pair, portfolio)
        self.five_min = ContinuousVWMA(300)
        self.eight_min = ContinuousVWMA(480)


    def __call__(self, tick):
        price, volume, timestamp = self.unpackTick(tick)

        self.five_min.update(price, volume, timestamp)
        self.eight_min.update(price, volume, timestamp)

        prev_crossover_time = self.prev_crossover_time
        prev_sell_time = self.prev_sell_time

        # @HARDCODE Volume of buy/sell
        if self.hasCash() and not self.hasBalance()  and self.five_min.avg > self.eight_min.avg:
            if prev_crossover_time is None:
                prev_crossover_time = timestamp
            elif timestamp - prev_crossover_time >= self.timelag_required:
                if timestamp - prev_sell_time >= 120:
                    self.marketbuy(1, '[Old strat]')
                    prev_crossover_time = None

        elif self.hasBalance() and self.five_min.avg < self.eight_min.avg:
            if prev_crossover_time is None:
                prev_crossover_time = timestamp
            elif timestamp - prev_crossover_time >= self.timelag_required:
                self.marketSell(1, '[Old strat]')
                prev_crossover_time = None
                prev_sell_time = timestamp
        else:
            prev_crossover_time = None

        self.prev_crossover_time = prev_crossover_time
        self.prev_sell_time = prev_sell_time


# @DEPRECATED
class RFStrat(Strategy):

    def __init__(self, pair, portfolio, message='[RF]', period=60, scope1=5, scope2=8):
        super().__init__(pair, portfolio)
        self.five_min = ContinuousVWMA(period * scope1)
        self.eight_min = ContinuousVWMA(period * scope2)
        self.message = message
        self.timelag_required = 30


    def __call__(self, tick):
        price, volume, timestamp = self.unpackTick(tick)

        self.five_min.update(price, volume, timestamp)
        self.eight_min.update(price, volume, timestamp)

        prev_tick_price = self.prev_tick_price
        prev_crossover_time = self.prev_crossover_time
        prev_sell_time = self.prev_sell_time

        if self.hasCash() and not self.hasBalance() and self.five_min.avg > self.eight_min.avg:
            logger.debug('RF identified uptrend')

            if prev_crossover_time is None:
                prev_crossover_time = timestamp
                prev_tick_price = price

            elif timestamp - prev_crossover_time >= self.timelag_required:
                logger.debug('RF identified last crossover was 30 secs ago')

                if timestamp - prev_sell_time >= 120 or price >= 1.0025 * prev_tick_price:

                    amount = self.portfolio.balance[self.pair]
                    self.marketBuy(amount, self.message)

                    prev_crossover_time = None
                    prev_tick_price = None

        elif self.hasBalance() and self.five_min.avg < self.eight_min.avg:
            logger.debug('RF identified downtrend')

            if prev_crossover_time is None:
                prev_crossover_time = timestamp

            elif timestamp - prev_crossover_time >= 5:

                amount = self.equity_at_risk * self.equity() / price
                self.marketSell(amount, appendTimestamp(self.message, timestamp))

                prev_crossover_time = None
                prev_sell_time = timestamp

        else:
            prev_crossover_time = None

        self.prev_crossover_time = prev_crossover_time
        self.prev_sell_time = prev_sell_time


# @DEPRECATED
class ATRStrat(Strategy):

    def __init__(self, pair, portfolio, exchange=None, message='[ATR]', period=60, scope1=5, scope2=8):
        super().__init__(pair, portfolio, exchange)
        self.five_min = ContinuousVWMA(period * scope1)
        self.eight_min = ContinuousVWMA(period * scope2)
        self.bar = CandleBar(period, scope1)

        self.message = message

        self.upper_atr = 0.5
        self.lower_atr = 0.35


    def __call__(self, tick):
        price, volume, timestamp = self.unpackTick(tick)

        self.five_min.update(price, volume, timestamp)
        self.eight_min.update(price, volume, timestamp)
        self.bar.update(price, timestamp)

        prev_crossover_time = self.prev_crossover_time
        prev_sell_time = self.prev_sell_time

        try:
            atr = self.bar.getAtr()
            belowatr = self.bar.WMA < price - self.lower_atr * atr
            aboveatr = min(self.bar.WMA, self.eight_period_bar.WMA) > price + self.upper_atr * atr
            uptrend = self.bar.WMA > self.eight_period_bar.WMA
            downtrend = self.bar.WMA < self.eight_period_bar.WMA
        except RuntimeWarning:
            return

        if self.hasCash() and not self.hasBalance() and uptrend and belowatr:
            logger.signal('ATR identified uptrend and below ATR band')
            if prev_crossover_time is None:
                prev_crossover_time = timestamp

            elif timestamp - prev_crossover_time >= self.timelag_required:

                amount = self.equity_at_risk * self.equity() / price
                self.marketBuy(amount, self.message)

                prev_crossover_time = None

        elif self.hasBalance() and (downtrend or aboveatr):
            logger.signal('ATR identified downtrend and above ATR band')

            if prev_crossover_time is None:
                prev_crossover_time = timestamp

            elif timestamp - prev_crossover_time >= self.timelag_required:

                amount = self.portfolio.balance[self.pair]
                self.marketSell(amount, appendTimestamp(self.message, timestamp))

                prev_crossover_time = None
                prev_sell_time = timestamp

        else:
            prev_crossover_time = None

        self.prev_crossover_time = prev_crossover_time
        self.prev_sell_time = prev_sell_time



class WMAStrat(Strategy):

    def __init__(self, pair, portfolio, exchange=None, message='[WMA]', period=180, scope1=5, scope2=8):
        super().__init__(pair, portfolio, exchange)
        self.bar = CandleBar(period)
        self.ATR_5 = ATR(self.bar, scope1)
        self.WMA_5 = WMA(self.bar, scope1)
        self.WMA_8 = WMA(self.bar, scope2)

        self.message = message

        self.upper_atr = 0.5
        self.lower_atr = 0.5

    def __call__(self, tick):
        price, volume, timestamp = self.unpackTick(tick)
        if self.init_time == 0:
            self.init_time = timestamp

        self.bar.update(price, timestamp)

        if timestamp < self.init_time + self.WMA_8.lookback * self.bar.period:
            return

        prev_crossover_time = self.prev_crossover_time
        prev_sell_time = self.prev_sell_time

        try:
            atr = self.ATR_5.atr
            belowatr = max(self.WMA_5.wma, self.WMA_8.wma) < price - self.lower_atr * atr
            aboveatr = min(self.WMA_5.wma, self.WMA_8.wma) > price + self.upper_atr * atr
        except RuntimeWarning:
            return

        uptrend   = self.WMA_5.wma > self.WMA_8.wma
        downtrend = self.WMA_5.wma < self.WMA_8.wma

        # @HARDCODE Buy/Sell message
        if self.hasCash() and not self.hasBalance() and uptrend and belowatr:
            logger.signal('WMA identified uptrend and below WMA band')
            if prev_crossover_time is None:
                prev_crossover_time = timestamp

            elif timestamp - prev_crossover_time >= self.timelag_required:

                amount = self.equity_at_risk * self.equity() / price
                self.marketBuy(amount, appendTimestamp(self.message, timestamp))

                prev_crossover_time = None

        elif self.hasBalance() and (downtrend or aboveatr):
            logger.signal('WMA identified downtrend and above WMA band')

            if prev_crossover_time is None:
                prev_crossover_time = timestamp

            elif timestamp - prev_crossover_time >= self.timelag_required:

                amount = self.portfolio.balance[self.pair]
                self.marketSell(amount, appendTimestamp(self.message, timestamp))

                prev_crossover_time = None
                prev_sell_time = timestamp

        else:
            prev_crossover_time = None

        self.prev_crossover_time = prev_crossover_time
        self.prev_sell_time = prev_sell_time



class MACDStrat(Strategy):

    def __init__(self, pair, portfolio, threshold=0.0001, exchange=None, message='[MACD]', period=180, scope1=4,
            scope2=8, scope3=3):
        super().__init__(pair, portfolio, exchange)
        self.message = message

        self.candle = CandleBar(period)
        self.ema1 = EMA(self.candle, scope1)
        self.ema2 = EMA(self.candle, scope2)
        self.MACD = MACD(self.ema1, self.ema2, scope3)
        self.threshold = threshold

        self.entered = False
        self.prev_trend = False


    def __call__(self, tick):

        price, volume, timestamp = self.unpackTick(tick)
        self.candle.update(price, timestamp)

        try:
            uptrend = self.MACD.macd > (self.MACD.ema3 + price*self.threshold)
            downtrend = self.MACD.macd < self.MACD.ema3
        except TypeError:
            return

        # Set the current trend value
        if uptrend:
            trend = 'up'
        elif downtrend:
            trend = 'down'
        else:
            self.prev_trend = 'none'
            return

        # Check if the trend has been the same since last tick
        if self.prev_trend == trend:
            return
        else:
            logger.info('Crossed ' + self.message)
            self.prev_trend = trend

        if not self.entered and self.hasCash() and uptrend and not self.hasBalance():
            amount = min(self.equity_at_risk * self.equity() / price, self.portfolio.cash)
            self.marketBuy(amount, appendTimestamp(self.message, timestamp))
            self.entered = True
            self.confirm_crossed = False

        elif self.entered and downtrend and self.hasBalance():
            amount = self.portfolio.balance[self.pair]
            self.marketSell(amount, appendTimestamp(self.message, timestamp))
            self.entered = False
            self.confirm_crossed = False


class WMAModStrat(Strategy):

    def __init__(self, pair, portfolio, exchange=None, message='[WMA Mod]', period=180, scope1=5, scope2=8):
        super().__init__(pair, portfolio, exchange)
        self.bar = CandleBar(period)
        self.ATR_5 = ATR(self.bar, scope1)
        self.WMA_5 = WMA(self.bar, scope1)
        self.WMA_8 = WMA(self.bar, scope2)

        self.message = message

        self.upper_atr = 0.5
        self.lower_atr = 0.5
        self.can_sell = False
        self.entry_time = None


    def __call__(self, tick):
        price, volume, timestamp = self.unpackTick(tick)
        self.bar.update(price, timestamp)
        if self.init_time == 0:
            self.init_time = timestamp

        if timestamp < self.init_time + self.WMA_8.lookback * self.bar.period:
            return

        prev_crossover_time = self.prev_crossover_time
        prev_sell_time      = self.prev_sell_time
        entry_time          = self.entry_time
        can_sell            = self.can_sell

        # @ta should not raise RuntimeWarning
        try:
            atr = self.ATR_5.atr

            belowatr = max(self.WMA_5.wma, self.WMA_8.wma) < price - self.lower_atr * atr
            aboveatr = min(self.WMA_5.wma, self.WMA_8.wma) > price + self.upper_atr * atr
        except RuntimeWarning:
            return

        uptrend   = self.WMA_5.wma > self.WMA_8.wma
        downtrend = self.WMA_5.wma < self.WMA_8.wma

        # @HARDCODE Buy/Sell message
        if self.hasCash() and not self.hasBalance() and belowatr:
            logger.signal('WMAMod identified uptrend and below ATR band')
            #if prev_crossover_time is None:
                #prev_crossover_time = timestamp

            #elif timestamp - prev_crossover_time >= self.timelag_required:

            amount = self.equity_at_risk * self.equity() / price
            self.marketBuy(amount, appendTimestamp(self.message, timestamp))

            prev_crossover_time = None

            if uptrend:
                can_sell = True
            elif downtrend:
                can_sell = False
            entry_time = timestamp

        elif self.hasBalance():
            if not can_sell and uptrend:
                can_sell = True
            elif (can_sell and downtrend) or (not can_sell and aboveatr):
                logger.signal('WMAMod identified downtrend')
                if prev_crossover_time is None:
                    prev_crossover_time = timestamp

                elif timestamp - prev_crossover_time >= self.timelag_required:

                    amount = self.portfolio.balance[self.pair]
                    self.marketSell(amount, appendTimestamp(self.message, timestamp))

                    prev_crossover_time = None
                    prev_sell_time = timestamp
                    entry_time = None

        else:
            prev_crossover_time = None

        self.prev_crossover_time = prev_crossover_time
        self.prev_sell_time = prev_sell_time
        self.entry_time = entry_time
        self.can_sell = can_sell


class WMAForceStrat(Strategy):

    def __init__(self, pair, portfolio, exchange=None, message='[WMA Force]', period=180, scope1=5, scope2=8):
        super().__init__(pair, portfolio, exchange)
        self.bar = CandleBar(period)
        self.ATR_5 = ATR(self.bar, scope1)
        self.WMA_5 = WMA(self.bar, scope1)
        self.WMA_8 = WMA(self.bar, scope2)
        self.vwma = ContinuousVWMA(period)

        self.message = message
        self.dollar_volume_flag = False

        self.upper_atr = 0.5
        self.lower_atr = 0.5
        self.can_sell = False
        self.v_sell = False
        self.entry_time = None
        self.prev_sell_time = None


    def __call__(self, tick):
        price, volume, timestamp = self.unpackTick(tick)
        tick = json.loads(tick)

        action = -1 * (tick['type'] * 2 - 1)

        self.bar.update(price, timestamp)
        self.vwma.update(price, timestamp, volume, action)

        if self.init_time == 0:
            self.init_time = timestamp

        if timestamp < self.init_time + self.WMA_8.lookback * self.bar.period:
            return

        prev_crossover_time = self.prev_crossover_time
        prev_sell_time = self.prev_sell_time
        entry_time = self.entry_time
        can_sell = self.can_sell
        dollar_volume_flag = self.dollar_volume_flag
        v_sell = self.v_sell

        # @ta should not raise RuntimeWarning
        try:
            atr = self.ATR_5.atr

            belowatr = max(self.WMA_5.wma, self.WMA_8.wma) < price - self.lower_atr * atr
            aboveatr = min(self.WMA_5.wma, self.WMA_8.wma) > price + self.upper_atr * atr
        except RuntimeWarning:
            return

        uptrend   = self.WMA_5.wma > self.WMA_8.wma
        downtrend = self.WMA_5.wma < self.WMA_8.wma

        buy_signal = False
        sell_signal = False
        v_sell_signal = False

        # @HARDCODE Buy/Sell message

        # Buy/Sell singal generation

        if self.hasCash() and not self.hasBalance():
            if v_sell:
                if uptrend or belowatr or aboveatr:
                    return
                elif downtrend:
                    v_sell = False
            elif belowatr:
                buy_signal = True
            else:
                prev_crossover_time = None

        elif self.hasBalance():
            if dollar_volume_flag and self.vwma.dollar_volume <= 0:
                v_sell_signal = True
                logger.signal("VWMA Indicate sell at: " + str(timestamp))
            elif not can_sell and aboveatr:
                sell_signal = True
            elif can_sell and downtrend:
                sell_signal = True
            elif not can_sell and uptrend:
                can_sell = True
            elif not can_sell and downtrend:
                return

        else:
            prev_crossover_time = None

        # Execution of signals
        if self.hasCash() and not self.hasBalance() and buy_signal:
            if prev_crossover_time is None:
                prev_crossover_time = timestamp

            elif timestamp - prev_crossover_time >= self.timelag_required:
                amount = self.equity_at_risk * self.equity() / price
                self.marketBuy(amount, appendTimestamp(self.message, timestamp), timestamp)

                prev_crossover_time = None

                if uptrend:
                    can_sell = True
                elif downtrend:
                    can_sell = False

        elif self.hasBalance() and v_sell_signal:
            amount = self.portfolio.balance[self.pair]
            self.marketSell(amount, appendTimestamp(self.message, timestamp), timestamp)

            prev_crossover_time = None
            dollar_volume_flag = False

            v_sell = True

        elif self.hasBalance() and sell_signal:

            if prev_crossover_time is None:
                prev_crossover_time = timestamp

            elif timestamp - prev_crossover_time >= self.timelag_required:

                amount = self.portfolio.balance[self.pair]
                self.marketSell(amount, appendTimestamp(self.message, timestamp), timestamp)

                prev_crossover_time = None
                dollar_volume_flag = False

        ####### Hardcoded for BCH volume

        if self.vwma.dollar_volume > 1.75 * (10**5):
            dollar_volume_flag = True
        elif self.vwma.dollar_volume < 0:
            dollar_volume_flag = False

        self.prev_crossover_time = prev_crossover_time
        self.prev_sell_time = prev_sell_time
        self.entry_time = entry_time
        self.can_sell = can_sell
        self.dollar_volume_flag = dollar_volume_flag
        self.v_sell = v_sell

class WMAForceBollingerStrat(Strategy):

    def __init__(self, pair, portfolio, exchange=None, message='[WMA Bollinger]', period=180, scope1=5, scope2=8, upper_atr=0.5, lower_atr=0.5, timeframe=3600, bband = 3.5, bband_period=20, vol_multipler=30, vwma_lb=40):
        self.indicators = {}

        self.indicators['bar'] = bar = CandleBar(period)
        self.ATR_5 = ATR(bar, scope1)
        self.WMA_5 = WMA(bar, scope1)
        self.WMA_8 = WMA(bar, scope2)
        self.indicators['vwma1'] = ContinuousVWMA(period * 3) # @HARDCODE
        self.indicators['vwma2'] = ContinuousVWMA(period * vwma_lb) # @HARDCODE
        self.sma_20 = SMA(bar, bband_period)
        self.bollinger = BollingerBand(self.sma_20, bband_period)

        self.message = message
        self.dollar_volume_flag = False

        self.timelag_required = 15
        self.bollinger_signal = False
        self.upper_atr = upper_atr
        self.lower_atr = lower_atr
        self.bband = bband
        self.timeframe = timeframe
        self.vol_multipler = vol_multipler
        self.can_sell = False
        self.v_sell = False
        self.tradable_window = 0
        self.init_time = 0
        self.buy_signal = False
        self.sell_signal = False
        self.v_sell_signal = False

        super().__init__(pair, portfolio, exchange)

    def generateSignal(self, price, timestamp, volume, action):

        if self.init_time == 0:
            self.init_time = timestamp

        if timestamp < self.init_time + max(self.WMA_8.lookback, 20) * self.bar.period:
            return

        # @ta should not raise RuntimeWarning
        try:
            atr = self.ATR_5.atr

            belowatr = max(self.WMA_5.wma, self.WMA_8.wma) < price - self.lower_atr * atr
            aboveatr = min(self.WMA_5.wma, self.WMA_8.wma) > price + self.upper_atr * atr
        except RuntimeWarning:
            return

        self.uptrend   = self.WMA_5.wma > self.WMA_8.wma
        self.downtrend = self.WMA_5.wma < self.WMA_8.wma

        self.buy_signal = False
        self.sell_signal = False
        self.v_sell_signal = False

        # @HARDCODE Buy/Sell message
        # @TODO should not trade the first signal if we enter the bollinger_signal with an uptrend?

        # Buy/Sell singal generation
        # Band confirmation
        norm_vol1 = self.vwma1.dollar_volume / self.vwma1.period
        norm_vol2 = self.vwma2.dollar_volume / self.vwma2.period

        # Dollar volume signal # hard code threshold for the moment
        if self.hasBalance() and  norm_vol1 > norm_vol2 * self.vol_multipler:
            self.dollar_volume_flag = True
        else:
            self.dollar_volume_flag = False

        if self.bollinger.band > self.bband: # currently snooping 3.5%
            self.bollinger_signal = True
            self.tradable_window = timestamp
        if timestamp > self.tradable_window + self.timeframe: # available at 1h trading window (3600s one hour)
            self.bollinger_signal = False

        if self.hasCash() and not self.hasBalance():
            if self.v_sell:
                if self.uptrend or belowatr or aboveatr:
                    return
                elif self.downtrend:
                    self.v_sell = False
            elif belowatr:
                self.buy_signal = True
            else:
                self.prev_crossover_time = None

        elif self.hasBalance():
            if self.dollar_volume_flag and self.vwma1.dollar_volume <= 0:
                self.v_sell_signal = True
                logger.signal("VWMA Indicate sell at: " + str(timestamp))
            elif not self.can_sell and aboveatr:
                self.sell_signal = True
            elif self.can_sell and self.downtrend:
                self.sell_signal = True
            elif not self.can_sell and self.uptrend:
                self.can_sell = True
            elif not self.can_sell and self.downtrend:
                return

        else:
            self.prev_crossover_time = None

    # @Regression: Timestamp/Price/unneccesary signals shouldn't be here
    # Execution of signals
    # Can only buy if buy_signal and bollinger_signal both exist
    def execute(self):
        if self.hasCash() and not self.hasBalance() and self.buy_signal and self.bollinger_signal:
            if self.prev_crossover_time is None:
                self.prev_crossover_time = self.timestamp # @Hardcode @Fix logic, do not use timestamp here

            elif self.timestamp - self.prev_crossover_time >= self.timelag_required:
                self.marketBuy(self.maxBuyAmount(), appendTimestamp(self.message, self.timestamp))

                self.prev_crossover_time = None
                # setting can_sell flag for preventing premature exit
                if self.uptrend:
                    self.can_sell = True
                elif self.downtrend:
                    self.can_sell = False

        # Sell immediately if v_sell signal is present, do not enter the position before next uptrend
        elif self.hasBalance() and self.v_sell_signal:
            self.marketSell(self.maxSellAmount(), appendTimestamp(self.message, self.timestamp))

            self.prev_crossover_time = None
            self.dollar_volume_flag = False

            self.v_sell = True

        elif self.hasBalance() and self.sell_signal:

            if self.prev_crossover_time is None:
                self.prev_crossover_time = self.timestamp

            elif self.timestamp - self.prev_crossover_time >= self.timelag_required:

                self.marketSell(self.maxSellAmount(), appendTimestamp(self.message, self.timestamp))

                self.prev_crossover_time = None
                self.dollar_volume_flag = False



# @TODO RSI is validated, strategy partially implemented
class WMABollingerRSIStrat(Strategy):

    def __init__(self, pair, portfolio, exchange=None, message='[WMA Bollinger]', period=180, scope1=5, scope2=8, upper_atr = 0.5, lower_atr = 0.5, timeframe = 3600, bband = 3.5, bband_period=20, vol_multipler = 30, vwma_la =3, vwma_lb = 40, rsi_la = 14):
        super().__init__(pair, portfolio, exchange)
        self.bar = CandleBar(period)
        self.ATR_5 = ATR(self.bar, scope1)
        self.WMA_5 = WMA(self.bar, scope1)
        self.WMA_8 = WMA(self.bar, scope2)
        self.vwma1 = ContinuousVWMA(period * vwma_la)
        self.vwma2 = ContinuousVWMA(period * vwma_lb)
        self.sma_20 = SMA(self.bar, bband_period)
        self.bollinger = BollingerBand(self.sma_20, bband_period)
        self.rsi = RSI(self.bar, rsi_la) # @HARDCODE

        self.message = message
        self.dollar_volume_flag = False

        self.bollinger_signal = False
        self.rsi_bsignal = False
        self.rsi_ssignal = False
        self.rsi_sell_flag = False
        self.upper_atr = upper_atr
        self.lower_atr = lower_atr
        self.bband = bband
        self.timeframe = timeframe
        self.vol_multipler = vol_multipler
        self.can_sell = False
        self.v_sell = False
        self.entry_time = None
        self.prev_sell_time = None
        self.tradable_window = 0


    def __call__(self, tick):
        price, volume, timestamp = self.unpackTick(tick)
        tick = json.loads(tick)

        action = -1 * (tick['type'] * 2 - 1)

        self.bar.update(price, timestamp)
        self.vwma1.update(price, timestamp, volume, action)
        self.vwma2.update(price, timestamp, volume, action)

        if self.init_time == 0:
            self.init_time = timestamp

        if timestamp < self.init_time + max(self.WMA_8.lookback, 20) * self.bar.period:
            return

        prev_crossover_time = self.prev_crossover_time
        prev_sell_time = self.prev_sell_time
        entry_time = self.entry_time
        can_sell = self.can_sell
        dollar_volume_flag = self.dollar_volume_flag
        v_sell = self.v_sell
        tradable_window = self.tradable_window
        bollinger_signal = self.bollinger_signal
        rsi_bsignal = self.rsi_bsignal
        rsi_ssignal = self.rsi_ssignal
        rsi_sell_flag = self.rsi_sell_flag

        # @ta should not raise RuntimeWarning
        try:
            atr = self.ATR_5.atr

            belowatr = max(self.WMA_5.wma, self.WMA_8.wma) < price - self.lower_atr * atr
            aboveatr = min(self.WMA_5.wma, self.WMA_8.wma) > price + self.upper_atr * atr
        except RuntimeWarning:
            return

        uptrend   = self.WMA_5.wma > self.WMA_8.wma
        downtrend = self.WMA_5.wma < self.WMA_8.wma

        buy_signal = False
        sell_signal = False
        v_sell_signal = False

        # @HARDCODE Buy/Sell message
        # @TODO should not trade the first signal if we enter the bollinger_signal with an uptrend?

        # Buy/Sell singal generation
        # Band confirmation
        norm_vol1 = self.vwma1.dollar_volume / self.vwma1.period
        norm_vol2 = self.vwma2.dollar_volume / self.vwma2.period

        # Dollar volume signal # hard code threshold for the moment
        if self.hasBalance() and  norm_vol1 > norm_vol2 * self.vol_multipler:
            self.dollar_volume_flag = True
        else:
            self.dollar_volume_flag = False

        if self.bollinger.band > self.bband: # currently snooping 3.5%
            bollinger_signal = True
            tradable_window = timestamp
        if timestamp > tradable_window + self.timeframe: # available at 1h trading window (3600s one hour)
            bollinger_signal = False

        # RSI signal generation
        if self.rsi.rsi > 50:
            if rsi_sell_flag:
                pass
            elif self.rsi.rsi >80:
                rsi_bsignal = True
                rsi_ssignal = False
                rsi_sell_flag = True
            else:
                rsi_bsignal = True
                rsi_ssignal = False

        if self.rsi.rsi < 60:
            if rsi_sell_flag:
                rsi_ssignal = True
                rsi_bsignal = False
            if self.rsi.rsi < 50:
                rsi_ssignal = True
                rsi_bsignal = False
                rsi_sell_flag = False

        if self.hasCash() and not self.hasBalance():
            if v_sell:
                if uptrend or belowatr or aboveatr:
                    return
                elif downtrend:
                    v_sell = False
            elif belowatr:
                buy_signal = True
            else:
                prev_crossover_time = None

        elif self.hasBalance():
            if dollar_volume_flag and self.vwma1.dollar_volume <= 0:
                v_sell_signal = True
                logger.signal("VWMA Indicate sell at: " + str(timestamp))
            elif not can_sell and aboveatr:
                sell_signal = True
            elif can_sell and downtrend:
                sell_signal = True
            elif not can_sell and uptrend:
                can_sell = True
            elif not can_sell and downtrend:
                return

        else:
            prev_crossover_time = None

        # Execution of signals
        # Can only buy if buy_signal and bollinger_signal both exist
        if self.hasCash() and not self.hasBalance() and buy_signal and bollinger_signal and rsi_bsignal:
            if prev_crossover_time is None:
                prev_crossover_time = timestamp

            elif timestamp - prev_crossover_time >= self.timelag_required:
                amount = self.equity_at_risk * self.equity() / price
                self.marketBuy(amount, appendTimestamp(self.message, timestamp), timestamp)

                prev_crossover_time = None
                # setting can_sell flag for preventing premature exit
                if uptrend:
                    can_sell = True
                elif downtrend:
                    can_sell = False
        # Sell immediately if v_sell signal is present, do not enter the position before next uptrend
        elif self.hasBalance() and v_sell_signal:
            amount = self.portfolio.balance[self.pair]
            self.marketSell(amount, appendTimestamp(self.message, timestamp), timestamp)

            prev_crossover_time = None
            dollar_volume_flag = False

            v_sell = True

        elif self.hasBalance() and sell_signal and rsi_ssignal:

            if prev_crossover_time is None:
                prev_crossover_time = timestamp

            elif timestamp - prev_crossover_time >= self.timelag_required:

                amount = self.portfolio.balance[self.pair]
                self.marketSell(amount, appendTimestamp(self.message, timestamp), timestamp)

                prev_crossover_time = None
                dollar_volume_flag = False

        ####### Hardcoded for BCH volume
        # Do not trigger take into account of v_sell unless in position


        self.bollinger_signal = bollinger_signal
        self.rsi_bsignal = rsi_bsignal
        self.rsi_ssignal = rsi_ssignal
        self.rsi_sell_flag = rsi_sell_flag
        self.tradable_window = tradable_window
        self.prev_crossover_time = prev_crossover_time
        self.prev_sell_time = prev_sell_time
        self.entry_time = entry_time
        self.can_sell = can_sell
        self.dollar_volume_flag = dollar_volume_flag
        self.v_sell = v_sell

# @In Progress
# Needs ATR x MA indicators
class SwissStrat(Strategy):
    def __init__(self, pair, portfolio, exchange=None, message='[Swiss]', period=180, atr_lb=5,
            wma1_lb=5, wma2_lb=8, ema1_lb=8, ema2_lb=15, macd_lb=5, threshold=0.00001, vwma_lb=10,
            sma_lb=20, bollinger_lb=20, bollinger_threshold=2.0, bollinger_window=3600,
            upperatr=0.3, loweratr=0.3):

        super().__init__(pair, portfolio, exchange)

        self.candle = CandleBar(period)
        self.atr  = ATR(self.candle, atr_lb)
        self.wma1 = WMA(self.candle, wma1_lb)
        self.wma2 = WMA(self.candle, wma2_lb)
        self.ema1 = EMA(self.candle, ema1_lb)
        self.ema2 = EMA(self.candle, ema2_lb)
        self.macd = MACD(self.ema1, self.ema2, macd_lb)
        self.vwma1 = ContinuousVWMA(period)
        self.vwma2 = ContinuousVWMA(period * vwma_lb)
        self.sma = SMA(self.candle, sma_lb)
        self.bollinger = BollingerBand(self.sma, bollinger_lb)

        self.message = message
        self.period = period
        self.threshold = threshold
        self.bollinger_threshold = bollinger_threshold
        self.bollinger_window = bollinger_window
        self.upperatr = upperatr
        self.loweratr = loweratr

        self.init_time = 0
        self.tradable_window = 0
        self.entered = None
        self.was_v_sell = False
        self.was_high_dollar_volume_flag = False


    def __call__(self, tick):
        price, volume, timestamp = self.unpackTick(tick)

        tick = json.loads(tick)
        action = -1 * (tick['type'] * 2 - 1)
        self.candle.update(price, timestamp)
        self.vwma1.update(price, timestamp, volume, action)
        self.vwma2.update(price, timestamp, volume, action)


        ## First tick initialisation
        if self.init_time == 0:
            self.init_time = timestamp
            return

        if timestamp < self.init_time + self.period * 8:
            return

        buy_signal = False
        sell_signal = False
        v_sell_signal = False


        ## Signal generation
        # ATR/MA signal
        atr = self.atr.atr
        belowatr = min(self.wma1.wma, self.wma2.wma) < price - self.loweratr * atr
        aboveatr = max(self.wma1.wma, self.wma2.wma) > price + self.upperatr * atr

        uptrend   = self.wma1.wma > self.wma2.wma
        downtrend = self.wma1.wma < self.wma2.wma

        # MACD signal
        try:
            if self.macd.macd > (self.macd.ema3 + price * self.threshold):
                macd_signal = True
            else:
                macd_signal = False
        except TypeError:
            return

        if not macd_signal and not belowatr:
            self.was_v_sell = False

        # Update bollinger tradable timeframe
        if self.bollinger.band > self.bollinger_threshold: # @Hardcode
            self.tradable_window = timestamp + self.bollinger_window # @Hardcode

        # Bollinger band signal
        if timestamp < self.tradable_window:
            bollinger_signal = True
        else:
            bollinger_signal = False

        norm_vol1 = self.vwma1.dollar_volume / self.vwma1.period
        norm_vol2 = self.vwma2.dollar_volume / self.vwma2.period

        # Dollar volume signal
        if norm_vol1 > norm_vol2 * 3:
            self.was_high_dollar_volume = True
        else:
            self.was_high_dollar_volume = False

        # Buy/sell finalise
        if bollinger_signal and macd_signal and belowatr and not self.was_v_sell:
            buy_signal = True

        if self.was_high_dollar_volume and self.vwma1.dollar_volume <= 0:
            v_sell_signal = True

        if belowatr and downtrend:
            sell_signal = True


        ## Handle signal
        if not self.entered and self.hasCash() and buy_signal:
            amount = self.maxBuyAmount(price)
            self.marketBuy(amount, self.message, timestamp)
            self.entered = True

        elif self.entered and v_sell_signal:
            amount = self.maxSellAmount()
            self.marketSell(amount, self.message, timestamp)
            self.entered = False
            self.was_v_sell = True

        elif self.entered and sell_signal:
            amount = self.maxSellAmount()
            self.marketSell(amount, self.message, timestamp)
            self.entered = False



# @In progress @Deprecated?
class VWMAStrat(Strategy):

    def __init__(self, pair, portfolio, exchange=None, message='', period=60, shorttrend=5, longtrend=10):
        super().__init__(pair, portfolio, exchange)
        self.message = message

        self.vwma = ContinuousVWMA(period * shorttrend)
        self.entered = False
        self.prev_trend = True
        self.amount = 0

    def __call__(self, tick):
        price, volume, timestamp = self.unpackTick(tick)
        # @HARDCODE @CHANAGE INTERFACE
        tick = json.loads(tick)

        action = -1 * (tick['type'] * 2 - 1)

        self.vwma.update(price, timestamp, volume, action)

        if self.prev_crossover_time == None:
            self.prev_crossover_time = timestamp
            return

        trend = self.shorttrend.avg > self.longtrend.avg

        # Checks if there has been a crossing of VWMA
        if self.prev_trend != trend:
            # Set new cross time and latest trend direction (True for up, False for down)
            self.prev_crossover_time = timestamp
            self.prev_trend = trend

            if trend: trend_str = 'upwards'
            else: trend_str = 'downwards'

            logger.debug('VWMA identified crossing ' + trend_str)
            return

        # Filter out temporary breakouts in either direction
        elif timestamp < self.prev_crossover_time + self.timelag_required:
            return

        # Confirm there has been a trend, set more readable variables
        else:
            confirm_up = trend
            confirm_down = not trend

        if not self.entered and self.hasCash() and confirm_up:
            self.amount = self.equity_at_risk * self.equity() / price
            self.marketBuy(self.amount, self.message)
            self.entered = True

        elif self.entered and confirm_down:
            self.marketSell(self.amount, self.message)
            self.entered = False


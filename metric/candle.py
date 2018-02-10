from .base import Metric
from .generic import *

import numpy as np


class Candle:
    '''Mutable candle stick with namedtuple-like API.'''

    def __init__(self, o, c, h, l, t, v):
        self._bar = [o, c, h, l, t, v]

    def __getitem__(self, item):
        return self._bar[item]

    def __repr__(self):
        return self._bar.__repr__()

    @property
    def open(self):
        return self._bar[0]

    @property
    def close(self):
        return self._bar[1]

    @property
    def high(self):
        return self._bar[2]

    @property
    def low(self):
        return self._bar[3]

    @property
    def timestamp(self):
        return self._bar[4]

    @property
    def volume(self):
        return self._bar[5]

    @open.setter
    def open(self, value):
        self._bar[0] = value

    @close.setter
    def close(self, value):
        self._bar[1] = value

    @high.setter
    def high(self, value):
        self._bar[2] = value

    @low.setter
    def low(self, value):
        self._bar[3] = value

    @timestamp.setter
    def timestamp(self, value):
        self._bar[4] = value

    @volume.setter
    def volume(self, value):
        self._bar[5] = value


class CandleBar:
    '''Container for candlesticks of a given length.

    Candle dependent metrics can be attached to a CandleBuffer instance. These
    metrics will then be pinged everytime a new candle is added to the buffer.
    Metrics must implement a ping() function which retrieves the newest candle
    from the buffer and update themselves accordingly.

    Args:
        period: Length of each candlestick of this collection
        maxcandles: Maximum number of historic candles to keep around

    Attributes:
        _bars: List of all the Candle objects
        _metrics: Metrics that are attached to the CandleBar instance
        _period: Length (time span) of each candlestick
        _maxsize: Maximum number of historic candles to keep around
    '''

    def __init__(self, period):
        self._bars = []
        self._metrics = []
        self.period = period
        self.last_timestamp = None


    def pushTick(self, price, timestamp, volume=0, action=0):
        '''Provides public interface for accepting ticks'''
        # initialise the candle collection
        if self.last_timestamp is None:
            self.last_timestamp = timestamp
            self._pushInitCandle(price, timestamp, volume)

        # append previous n candles if no tick arrived in between
        elif self.barIndex(timestamp) != self.barIndex(self.last_timestamp):
            tmp_ts = self.last_timestamp + self.period
            while self.barIndex(tmp_ts) < self.barIndex(timestamp):
                self._pushEmptyCandle(self.last_close, tmp_ts)
                tmp_ts += self.period

            self._pushInitCandle(price, timestamp, volume)
            self.last_timestamp = timestamp

        # if tick arrived before next time period, update current candle
        elif self.barIndex(timestamp) == self.barIndex(self.last_timestamp):
            self.last_low = min(self.last_low , price)
            self.last_high = max(self.last_high, price)
            self.last_close = price
            self.last_volume += volume

        # No one uses it yet so removed for reducing overhead
        #self._broadcastTick(price, timestamp, volume, action)


    def pushCandle(self, o, c, h, l, t, v):
        '''Provides public interface for accepting aggregated candles'''
        self._pushFullCandle(o, c, h, l, t, v)


    def attach(self, metric):
        self._metrics.append(metric)


    def barIndex(self, timestamp):
        return int(timestamp / self.period)


    def prune(self, size):
        try:
            self._bars = self._bars[-size:]
        except IndexError:
            raise ("Empty CandleBar cannot be pruned")


    def open_prices(self, num_candles):
        return [x.open for x in self[-num_candles:]]


    def close_prices(self, num_candles):
        return [x.close for x in self[-num_candles:]]


    def _pushFullCandle(self, o, c, h, l, t, v):
        self._bars.append(Candle(o, c, h, l, t, v))
        self._broadcastCandle()


    def _pushInitCandle(self, price, timestamp, volume):
        self._bars.append(Candle(price, price, price, price, self.barIndex(timestamp), volume))
        self._broadcastCandle()


    def _pushEmptyCandle(self, price, timestamp):
        self._bars.append(Candle(price, price, price, price, self.barIndex(timestamp), 0))
        self._broadcastCandle()


    def _broadcastCandle(self):
        for metric in self._metrics:
            metric.onCandle
            try:
                metric.onCandle()
            except NotImplementedError:
                pass


    def _broadcastTick(self, price, ts, volume, action):
        for metric in self._metrics:
            try:
                metric.onTick(price, ts, volume, action)
            except NotImplementedError:
                pass

    def __len__(self, ):
        return len(self._bars)

    def __getitem__(self, item):
        return self._bars[item]

    @property
    def last_open(self):
        return self._bars[-1].open

    @property
    def last_close(self):
        return self._bars[-1].close

    @property
    def last_high(self):
        return self._bars[-1].high

    @property
    def last_low(self):
        return self._bars[-1].low

    @property
    def last_volume(self):
        return self._bars[-1].volume

    @last_open.setter
    def last_open(self, value):
        self._bars[-1].open = value

    @last_close.setter
    def last_close(self, value):
        self._bars[-1].close = value

    @last_high.setter
    def last_high(self, value):
        self._bars[-1].high = value

    @last_low.setter
    def last_low(self, value):
        self._bars[-1].low = value

    @last_volume.setter
    def last_volume(self, value):
        self._bars[-1].volume = value


class CandleMetric(Metric):
    '''Base class for candle dependent metrics'''

    def __init__(self, candle):
        self.candle = candle
        self.value = 0
        candle.attach(self)

    def onCandle(self):
        raise NotImplementedError('Base class does not register callbacks')

    def onTick(self, price, ts, volume, action):
        raise NotImplementedError('Base class does not register callbacks')


class SMA(CandleMetric):
    '''Calculate and store the latest SMA value for the attached candle'''

    def __init__(self, candle, lookback, use_open=True):
        super().__init__(candle)
        self._use_open = use_open
        self._lookback = lookback

    def onCandle(self):
        if len(self.candle) < self._lookback:
            return
        if self._use_open:
            prices = self.candle.open_prices(self._lookback)
        else:
            prices = self.candle.close_prices(self._lookback)
        self.value = np.mean(prices)

    def onTick(self, price, ts, volume, action):
        raise NotImplementedError # Not yet implemented


class WMA(CandleMetric):
    '''Calculate and store the latest WMA value for the attached candle'''

    def __init__(self, candle, lookback, use_open=True, weight=None):
        super().__init__(candle)
        self._use_open = use_open
        self._lookback = lookback
        self._weight = weight or [2 * (i + 1)/(lookback * (lookback + 1)) for i in range(lookback)]

    def onCandle(self):
        if len(self.candle) < self._lookback:
            return
        if self._use_open:
            prices = self.candle.open_prices(self._lookback)
        else:
            prices = self.candle.close_prices(self._lookback)
        self.value = np.average(prices, axis=0, weights=self._weight)

    def onTick(self, price, ts, volume, action):
        raise NotImplementedError # Not yet implemented


class EMA(CandleMetric):
    '''Calculate and store the latest EMA value for the attached candle'''

    def __init__(self, candle, lookback, use_open=True):
        super().__init__(candle)
        self._use_open = use_open
        self._lookback = lookback
        self._weight = 2 / (lookback + 1)

    def onCandle(self):
        price = self.candle.last_open if self._use_open else self.candle.last_close
        if self.value == 0:
            self.value = price
        else:
            self.value = price * self._weight + (1 - self._weight) * self.value

    def onTick(self, price, ts, volume, action):
        raise NotImplementedError # Not yet implemented


class RSI(CandleMetric):
    '''Calculate and store the latest RSI value for the attached candle'''

    def __init__(self, candle, lookback, use_open=True):
        super().__init__(candle)
        self._use_open = use_open
        self._lookback = lookback
        self._weight = 1 / lookback # MODIFIED to suit our purpose
        self.up = []
        self.down = []
        self.ema_up = None
        self.ema_down = None

    def onCandle(self):
        if len(self.candle) < 2:
            return

        if self._use_open:
            if (self.candle.last_open > self.candle[-2].open):
                self.up.append(abs(self.candle.last_open - self.candle[-2].open))
                self.down.append(0)
            else:
                self.down.append(abs(self.candle[-2].open - self.candle.last_open))
                self.up.append(0)
        else:
            if (self.candle.last_open > self.candle[-2].open):
                self.up.append(abs(self.candle.last_open - self.candle[-2].open))
                self.down.append(0)
            else:
                self.down.append(abs(self.candle[-2].open - self.candle.last_open))
                self.up.append(0)

        if len(self.up) < self._lookback:
            return

        price_up = self.up[-1]
        price_down = self.down[-1]

        # Initialization of ema_up and ema_down by simple averaging the up/down lists
        if self.ema_up == None and self.ema_down == None:
            self.ema_up = sum([x for x in self.up]) / len(self.up)
            self.ema_down = sum([x for x in self.down]) / len(self.down)

            try:
                self.value = 100 - 100 / (1 +  self.ema_up/self.ema_down)
            except ZeroDivisionError:
                if self.ema_down == 0 and self.ema_up != 0:
                    self.value = 100
                elif self.ema_up == 0 and self.ema_down != 0:
                    self.value = 0
                elif self.ema_up == 0 and self.ema_down == 0:
                    self.value = 50
            return

        # Update ema_up and ema_down according to logistic updating formula
        self.ema_up = self._weight * price_up + (1 - self._weight) * self.ema_up
        self.ema_down = self._weight * price_down + (1 - self._weight) * self.ema_down

        # Handling edge cases and return the RSI index according to formula
        try:
            self.value = 100 - 100 / (1 +  self.ema_up/self.ema_down)
        except ZeroDivisionError:
            if self.ema_down == 0 and self.ema_up != 0:
                self.value = 100
            elif self.ema_up == 0 and self.ema_down != 0:
                self.value = 0
            elif self.ema_up == 0 and self.ema_down == 0:
                self.value = 50

    def onTick(self, price, ts, volume, action):
        raise NotImplementedError # Not yet implemented


class MACD(CandleMetric):
    '''Calculate and store the latest MACD value for the attached candle.

    The value of self.value (inherited from Metric) is set to be the difference
    between the difference of two moving averages and the moving average of this
    difference.

    Args:
        candle: The underlying CandleBar instance
        fast: Instance of moving average with shorter lookback
        slow: Instance of moving average with longer lookback
        lookbac: Number of bars to consider for the difference moving average
        weights: Weighting to average the MA difference. Defaults to linear sequence
    '''

    def __init__(
            self,
            fast,
            slow,
            lookback,
            weights=None):
        assert fast.candle == slow.candle # @Use proper error
        super().__init__(fast.candle)
        self._fast = fast
        self._slow = slow
        self._lookback = lookback
        self._weights = weights or [2 * (i + 1) / (lookback * (lookback + 1)) for i in range(lookback)]
        self._past = []

    def onCandle(self):
        self.diff = self._fast - self._slow
        self._past.append(self.diff)
        self._past = self._past[-self._lookback:]

        if len(self._past) == self._lookback:
            self.diff_ma = np.average(self._past, axis=0, weights=self._weights)
            self.value = self.diff - self.diff_ma

    def onTick(self, price, ts, volume, action):
        raise NotImplementedError # Not yet implemented


class ATR(CandleMetric):

    def __init__(self, candle, lookback, use_open=True):
        super().__init__(candle)
        self._use_open = use_open
        self._lookback = lookback
        self._init = []
        self.value = 1000000000

    def onCandle(self):
        if len(self._init) < self._lookback + 1:
            self._init.append(self.candle.last_high - self.candle.last_low)
            self.value = sum(self._init) / len(self._init)
        else:
            t1 = self.candle[-2].high - self.candle[-2].low
            t2 = abs(self.candle[-2].high - self.candle[-3].close)
            t3 = abs(self.candle[-2].low - self.candle[-3].close)
            tr = max(t1, t2, t3)
            self.value = (self.value * (self._lookback - 1) + tr) / self._lookback

    def onTick(self, price, ts, volume, action):
        raise NotImplementedError # Not yet implemented


class BollingerBand(CandleMetric):
    '''Bollinger band

    Args:
        ma: Moving average to based upon
        upper_sd: Upper band standard deviation
        lower_sd: Lower band standard deviation
        lookback: Number of historic bars to consider for standard deviation

    Attributes:
        width: Standard deviation
        upperband: Price at top of the bollinger band
        lowerband: Price at bottom of the bollinger band
        band: Percent difference between price of the top of band and bottom of band
        value: Proxy for the band attribute
    '''

    def __init__(
            self,
            ma,
            lookback,
            use_open=True,
            sd=2,
            upper_sd=None,
            lower_sd=None):

        super().__init__(ma.candle)
        self.ma = ma
        self._use_open = use_open
        self._lookback = lookback
        self._upper_sd = upper_sd or sd
        self._lower_sd = lower_sd or sd

    def onCandle(self):
        if len(self.candle) < self._lookback:
            return

        if self._use_open:
            prices = self.candle.open_prices(self._lookback)
        else:
            prices = self.candle.close_prices(self._lookback)

        self.width = np.std(prices)
        self.upperband = self.ma + self._upper_sd * self.width
        self.lowerband = self.ma - self._lower_sd * self.width
        self.band = ((self.upperband / self.lowerband) - 1) * 100
        self.value = self.band

    def onTick(self, price, ts, volume, action):
        raise NotImplementedError # Not yet implemented


class MABollinger(CandleMetric):
    '''Moving average impose on bollinger band

    Args:
        bband: An instance of BollingerBand
        lookback: Lookback of the moving average
        weights: Weighting for averaging the Bollinger Band. Defaults to None (simple average).
    '''

    def __init__(self,
            bband,
            lookback,
            use_open=True,
            weights=None):

        super().__init__(bband.candle)
        self._use_open = use_open
        self._lookback = lookback
        self._weights = weights
        self._bband = bband
        self._bands = []

    def onCandle(self):
        if self._bband == 0:
            return

        self._bands.append(self._bband.value)

        if self._weights is None:
            self.value = np.mean(self._bands[-self._lookback:])
        else:
            self.value = np.average(self._weights, axis=0, weights=self._weight)

    def onTick(self, price, ts, volume, action):
        raise NotImplementedError # Not yet implemented

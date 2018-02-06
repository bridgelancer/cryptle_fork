from .base import Metric
from .generic import *


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
        _maxsize: Maximum number of historic candles to keep around
    '''

    def __init__(self, period, maxcandles=500):
        self._bars = []
        self._metrics = []
        self._period = period
        self._maxsize = maxcandles
        self.last_timestamp = None


    def pushTick(self, price, timestamp, volume=0, action=0):
        '''Provides public interface for accepting ticks'''
        # initialise the candle collection
        if self.last_timestamp is None:
            self.last_timestamp = timestamp
            self._pushInitCandle(price, timestamp, volume)

        # append previous n candles if no tick arrived in between
        elif self.barIndex(timestamp) != self.barIndex(self.last_timestamp):
            tmp_ts = self.last_timestamp + self._period
            while self.barIndex(tmp_ts) < self.barIndex(timestamp):
                self._pushEmptyCandle(self.last_close, tmp_ts)
                tmp_ts += self._period

            self._pushInitCandle(price, timestamp, volume)
            self.last_timestamp = timestamp

        # if tick arrived before next time period, update current candle
        elif self.barIndex(timestamp) == self.barIndex(self.last_timestamp):
            self.last_low = min(self.last_low , price)
            self.last_high = max(self.last_high, price)
            self.last_close = price
            self.last_volume += volume

        self._broadcastTick(price, timestamp, volume, action)
        self.prune(self._maxsize)


    def pushCandle(self, o, c, h, l, t, v):
        '''Provides public interface for accepting aggregated candles'''
        self._pushFullCandle(o, c, h, l, t, v)


    def attach(self, metric):
        self._metrics.append(metric)


    def barIndex(self, timestamp):
        return int(timestamp / self._period)


    def prune(self, size):
        try:
            self._bars = self._bars[-size:]
        except IndexError:
            raise ("Empty CandleBar cannot be pruned")


    def _pushFullCandle(self, o, c, h, l, t, v):
        self._bars.append(Candle(o, c, h, l, t, v))
        self._broadcastCandle()


    def _pushInitCandle(self, price, timestamp, volume):
        self._bars.append(Candle(price, price, price, price, self.barIndex(timestamp), volume))
        self._broadcastCandle()


    def _pushEmptyCandle(self, price, label):
        self._bars.append(Candle(price, price, price, price, self.barIndex(timestamp), 0))
        self._broadcastCandle()


    def _broadcastCandle(self):
        for metric in self._metrics:
            try:
                metric.onCandle()
            except AttributeError:
                pass


    def _broadcastTick(self, price, ts, volume, action):
        for metric in self._metrics:
            try:
                metric.onTick(price, ts, volume, action)
            except AttributeError:
                pass


    def __getitem__(self, item):
        return self._bars[item]

    def __len__(self):
        return len(self._bars)

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
        self._candle = candle
        self._value = 0
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
        if self._use_open:
            self._value = simple_moving_average([x.open for x in self._candle[-lookback:]], lookback)[0]
        else:
            self._value = simple_moving_average([x.close for x in self._candle[-lookback:]], lookback)[0]
    def onTick(self, price, ts, volume, action):
        return # Not yet implemented


class EMA(CandleMetric):
    '''Calculate and store the latest EMA value for the attached candle'''

    def __init__(self, candle, lookback, use_open=True):
        super().__init__(candle)
        self._use_open = use_open
        self._lookback = lookback


    def onCandle(self):
        if self._use_open:
            self._value = ema([x.open for x in self._candle[-self._lookback:]], self._lookback)[0]
        else:
            self._value = ema([x.close for x in self._candle[-self._lookback:]], self._lookback)[0]
    def onTick(self, price, ts, volume, action):
        return # Not yet implemented

class WMA(CandleMetric):
    '''Calculate and store the latest WMA value for the attached candle'''

    def __init__(self, candle, lookback, use_open=True):
        super().__init__(candle)
        self._use_open = use_open
        self._lookback = lookback

    def onCandle(self):
        if self._use_open:
            self._value = wma([x.open for x in self._candle[-self._lookback:]], self._lookback)[0]
        else:
            self._value = wma([x.close for x in self._candle[-self._lookback:]], self._lookback)[0]
    def onTick(self, price, ts, volume, action):
        return # Not yet implemented

# Not validated
class RSI(CandleMetric):
    '''Calculate and store the latest RSI value for the attached candle'''

    def __init__(self, candle, lookback, use_open=True):
        super().__init__(candle)
        self._use_open = use_open
        self._lookback = lookback
        self.up = []
        self.down = []
        self.ema_up = None
        self.ema_down = None
        self.weight = 1 / lookback # MODIFIED to suit our purpose
        self.rsi = 0

    def onCandle(self):
        if len(self._candle.bars) < 2:
            return
        else:
            pass

        if self._use_open:
            if (self._candle[-1].open > self._candle[-2].open):
                self.up.append(abs(self._candle[-1].open - self._candle[-2].open))
                self.down.append(0)
            else:
                self.down.append(abs(self._candle[-2].open - self._candle[-1].open))
                self.up.append(0)
        else:
            if (self._candle[-1].open > self._candle[-2].open):
                self.up.append(abs(self._candle[-1].open - self._candle[-2].open))
                self.down.append(0)
            else:
                self.down.append(abs(self._candle[-2].open - self._candle[-1].open))
                self.up.append(0)

        if len(self.up) < self.lookback:
            return
        else:
            pass

        price_up = self.up[-1]
        price_down = self.down[-1]

        # Initialization of ema_up and ema_down by simple averaging the up/down lists
        if self.ema_up == None and self.ema_down == None:
            self.ema_up = sum([x for x in self.up]) / len(self.up)
            self.ema_down = sum([x for x in self.down]) / len(self.down)

            try:
                self.rsi = 100 - 100 / (1 +  self.ema_up/self.ema_down)
            except ZeroDivisionError:
                if self.ema_down == 0 and self.ema_up != 0:
                    self.rsi = 100
                elif self.ema_up == 0 and self.ema_down != 0:
                    self.rsi = 0
                elif self.ema_up == 0 and self.ema_down == 0:
                    self.rsi = 50
            return
        else:
            pass

        # Update ema_up and ema_down according to logistic updating formula
        self.ema_up = self.weight * price_up + (1 - self.weight) * self.ema_up
        self.ema_down = self.weight * price_down + (1 - self.weight) * self.ema_down

        # Handling edge cases and return the RSI index according to formula
        try:
            self.rsi = 100 - 100 / (1 +  self.ema_up/self.ema_down)
        except ZeroDivisionError:
            if self.ema_down == 0 and self.ema_up != 0:
                self.rsi = 100
            elif self.ema_up == 0 and self.ema_down != 0:
                self.rsi = 0
            elif self.ema_up == 0 and self.ema_down == 0:
                self.rsi = 50
    def onTick(self, price, ts, volume, action):
        return # Not yet implemented

# Not validated
class MACD(CandleMetric):

    def __init__(self, candle, fast, slow, signal, use_open=True, roll_method=wma):
        super().__init__(candle)
        self._use_open = use_open
        self._roll_method = roll_method
        self._fast = fast
        self._slow = slow
        self._signal = signal
        self.diff = None
        self.output = None

    def onCandle(self):
        if len(self.candle.bars) < self._slow:
            return
        else:
            pass

        if self._use_open:
            series = [x.open for x in self._candle[-self._slow:]]

            result = macd(series, self._fast, self._slow, self._signal, roll_method = weighted_moving_average)

            diff, output = zip(*result)
            self.diff = diff
            self.output = output
    def onTick(self, price, ts, volume, action):
        return # Not yet implemented

# Not validated
class ATR(CandleMetric):
    def __init__(self, candle, lookback, use_open=True):
        super().__init__(candle)
        self._use_open = use_open
        self._lookback = lookback
        self._value = 1000000000
        self._init = []

    def onCandle(self):
        if len(self._init) < self._lookback + 1:
            self._init.append(self)
            self._value = sum(self._init) / len(self._init)
        else:
            t1 = self._candle[-2].max - self._candle[-2].min
            t2 = abs(self._candle[-2].max - self._candle[-3].close)
            t3 = abs(self._candle[-2].min - self._candle[-3].close)
            tr = max(t1, t2, t3)
            self._value = (self._value * (self._lookback - 1) + tr) / self._lookback
    def onTick(self, price, ts, volume, action):
        return # Not yet implemented

# Not validated
class BollingerBand(CandleMetric):
    def __init__(self, candle, lookback, use_open=True):
        super().__init__(candle)
        self._use_open = use_open
        self._lookback = lookback
        self.width = None
        self.upperband = None
        self.lowerband = None
        self.band = None

    def onCandle(self):
        if len(self._candle) < self._lookback:
            return
        else:
            pass

        if self._use_open:
            ls = [x.open for x in self._candle[-self._lookback:]]
            self.width = bollinger_width(ls, self._lookback, roll_method = sma)
            self.upperband = bollinger_up(ls, self._lookback, sd = 2, roll_method = sma)
            self.lowerband = bollinger_low(ls, self._lookback, sd = 2, roll_method = sma)
            self.band = bollinger_band(ls, self._lookback, sd = 2, roll_method = sma)
        else:
            ls = [x.close for x in self._candle[-self._lookback:]]
            self.width = bollinger_width(ls, self._lookback, roll_method = sma)
            self.upperband = bollinger_up(ls, self._lookback, sd = 2, roll_method = sma)
            self.lowerband = bollinger_low(ls, self._lookback, sd = 2, roll_method = sma)
            self.band = bollinger_band(ls, self._lookback, sd = 2, roll_method = sma)
    def onTick(self, price, ts, volume, action):
        return # Not yet implemented

# Not validated
class BNB(CandleMetric):
    def __init__(self, candle, primary, lookback, use_open=True):
        super().__init__(candle)
        self._use_open = use_open
        self._primary = primary
        self._lookback = lookback
        self._band = []

    def onCandle(self):
        if len(self._candle) < self._primary:
            return
        else:
            pass

        if self._use_open:
            ls = [x.open for x in self._candle[-self._primary:]]
            self._band.append(bollinger_band(ls, self._primary, sd = 2, roll_method=sma))
            if len(self._band) < self._lookback:
                return
            else:
                self.bnb = bollinger_up(self._band, self._lookback, sd = 1, roll_method=sma)
                self._band.pop()
        else:
            ls = [x.close for x in self._candle[-self._primary:]]
            self._band.append(bollinger_band(ls, self._primary, sd = 2, roll_method=sma))
            if len(self._band) < self._lookback:
                return
            else:
                self.bnb = bollinger_up(self._band, self._lookback, sd = 1, roll_method=sma)
                self._band.pop()
    def onTick(self, price, ts, volume, action):
        return # Not yet implemented




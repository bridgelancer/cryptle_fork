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
        self._last_timestamp = None
        self._maxsize = maxcandles


    def pushTick(self, price, timestamp, volume=0, action=0):
        '''Provides public interface for accepting ticks'''
        # initialise the candle collection
        if self._last_timestamp is None:
            self._last_timestamp = timestamp
            self._pushInitCandle(price, timestamp, volume)

        # append previous n candles if no tick arrived in between
        elif self.barIndex(timestamp) != self.barIndex(self._last_timestamp):
            tmp_ts = self._last_timestamp + self.period
            while self.barIndex(tmp_ts) < self.barIndex(timestamp):
                self._pushEmptyCandle(self.last_close, tmp_ts)
                tmp_ts += self.period

            self._pushInitCandle(price, timestamp, volume)
            self._last_timestamp = timestamp

        # if tick arrived before next time period, update current candle
        elif self.barIndex(timestamp) == self.barIndex(self.last_timestamp):
            self.last_low = min(self.last_low , price)
            self.last_hi = max(self.last_hi, price)
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
        return int(timestamp / self.period)


    def _pushFullCandle(self, o, c, h, l, t, v):
        self._bars.append(Candle(o, c, h, l, t, v))
        self._broadcastCandle()


    def _pushInitCandle(self, price, timestamp, volume):
        self._bars.append(Candle(price, price, price, price, self.barIndex(timestamp), volume))
        self._broadcastCandle()


    def _pushEmptyCandle(self, price, label):
        self._bars.append(Candle(price, price, price, price, self.barIndex(timestamp), 0))
        self._broadcastCandle()


    def _prune(self, size):
        try:
            self.bars = self.bars[-size:]
        except IndexError:
            raise ("Empty CandleBar cannot be pruned")


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
        return len(self.bars)

    @property
    def last_open(self):
        return self.bars[-1].open

    @property
    def last_close(self):
        return self.bars[-1].close

    @property
    def last_high(self):
        return self.bars[-1].high

    @property
    def last_low(self):
        return self.bars[-1].low

    @property
    def last_volume(self):
        return self.bars[-1].volume

    @last_open.setter
    def last_open(self, value):
        self.bars[-1].open = value

    @last_close.setter
    def last_close(self, value):
        self.bars[-1].close = value

    @last_high.setter
    def last_high(self, value):
        self.bars[-1].high = value

    @last_low.setter
    def last_low(self, value):
        self.bars[-1].low = value

    @last_volume.setter
    def last_volume(self, value):
        self.bars[-1].volume = value


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


    def onCandle(self):
        if self._use_open:
            self._value = simple_moving_average([x.open for x in self._candle[-lookback:]], lookback)[0]
        else:
            self._value = simple_moving_average([x.close for x in self._candle[-lookback:]], lookback)[0]


class EMA(CandleMetric):
    '''Calculate and store the latest EMA value for the attached candle'''

    def __init__(self, candle, lookback):
        super().__init__(candle)


    def onCandle(self):
        if self._use_open:
            self._value = weighted_moving_average([x.open for x in self._candle[-lookback:]], lookback)[0]
        else:
            self._value = weighted_moving_average([x.close for x in self._candle[-lookback:]], lookback)[0]

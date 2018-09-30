from metric.base import Candle
from cryptle.event import source, on

class Aggregator:
    '''An implementation of the generic candle aggregator.

    Aggregator is a class that converts tick values of either prices or Timeseries values to candle
    bar representation. It contains a subset of the functions of the CandleBar class in candle.py as
    it handles the aggregation of tick data to bar representation. This class is also an extension
    of the original CandleBar as it is designed to handle any tick-based value upon suitable wiring
    of interfaces. This class could also accept bar representation of data.

    '''

    def __init__(self, period, auto_prune=False, maxsize=500):
        self.period         = period
        self._bars          = [] # this construct might be unnecessary
        self._auto_prune    = auto_prune
        self._maxsize       = maxsize
        self.last_timestamp = None

    @on('tick')
    def pushTick(self, data):
        '''Provides public interface for accepting ticks. Tick (in list) should have value, volume, timestamp
        and action as the format'''
        if len(data) == 4:
            value, volume, timestamp, action = data[0], data[1], data[2], data[3]
        else:
            return NotImplementedError

        self.last_timestamp = timestamp

        # initialise the candle collection
        if self.last_bar is None:
            self._pushInitCandle(value, timestamp, volume, action)
            return

        # if tick arrived before next bar, update current candle
        if self._is_updated(timestamp):
            self.last_low   = min(self.last_low, value)
            self.last_high  = max(self.last_high, value)
            self.last_close = value
            self.last_volume += volume
            self.last_netvol += volume * action

        else:
            while not self._is_updated(timestamp - self.period):
                self._pushEmptyCandle(self.last_close, self.last_bar_timestamp + self.period)
            self._pushInitCandle(value, timestamp, volume, action)

    def _is_updated(self, timestamp):
        return timestamp <= self.last_bar_timestamp + self.period

    def _is_due(self, timestamp):
        return timestamp > self.last_bar_timestamp + self.period

    def prune(self, size):
        try:
            self._bars = self._bars[-size:]
        except IndexError:
            raise ("Empty CandleBar cannot be pruned")

    @on('candle')
    def pushCandle(self, bar):
        '''Provides public interface for accepting aggregated candles. '''
        self._pushFullCandle(*bar)
        # methods that output corresponding events to message bus
        self._pushAllMetrics(*bar)

    def _pushAllMetrics(self, o, c, h, l, t, v, nv):
        self._pushOpen(o)
        self._pushClose(c)
        self._pushHigh(h)
        self._pushLow(l)
        self._pushTime(t)
        self._pushVolume(v)
        self._pushNetVolume(nv)


    @source('aggregator:new_open')
    def _pushOpen(self, o):
        return o

    @source('aggregator:new_close')
    def _pushClose(self, c):
        return c

    @source('aggregator:new_high')
    def _pushHigh(self, h):
        return h

    @source('aggregator:new_low')
    def _pushLow(self, l):
        return l

    @source('aggregator:new_timestamp')
    def _pushTime(self, t):
        return t

    @source('aggregator:new_volume')
    def _pushVolume(self, v):
        return v

    @source('aggregator:new_net_volume')
    def _pushNetVolume(self, nv):
        return nv

    @source('aggregator:new_candle')
    def _pushInitCandle(self, value, timestamp, volume, action):
        round_ts = timestamp - timestamp % self.period
        new_candle = Candle(value, value, value, value, round_ts, volume, volume * action)
        self._bars.append(new_candle)
        #if len(self._bars) > 1:
        #    finished_candle = self._bars[-2]
        #    self._pushAllMetrics(finished_candle.open, finished_candle.close, finished_candle.high,
        #            finished_candle.low, finished_candle.timestamp, finished_candle.volume,
        #            finished_candle.netvol)
        #    return self._bars[-2]._bar
        #else:
        #    self._pushAllMetrics(value, value, value, value, round_ts, volume, volume * action)
        #    return new_candle._bar

        self._pushAllMetrics(value, value, value, value, round_ts, volume, volume * action)
        return new_candle._bar

    @source('aggregator:new_candle')
    def _pushFullCandle(self, o, c, h, l, t, v, nv):
        t = t - t % self.period
        new_candle = Candle(o, c, h, l, t, v, nv)
        self._bars.append(new_candle)
        self._pushAllMetrics(o, c, h, l, t, v, nv)
        return new_candle._bar

    @source('aggregator:new_candle')
    def _pushEmptyCandle(self, value, timestamp):
        round_ts = timestamp - timestamp % self.period
        new_candle = Candle(value, value, value, value, round_ts, 0, 0)
        self._bars.append(new_candle)
        self._pushAllMetrics(value, value, value, value, round_ts, 0, 0)
        return new_candle

    @property
    def last_bar(self):
        try:
            return self._bars[-1]
        except IndexError:
            return None

    @property
    def last_open(self):
        return self.last_bar.open

    @property
    def last_close(self):
        return self.last_bar.close

    @property
    def last_high(self):
        return self.last_bar.high

    @property
    def last_low(self):
        return self.last_bar.low

    @property
    def last_bar_timestamp(self):
        return self.last_bar.timestamp

    @property
    def last_volume(self):
        return self.last_bar.volume

    @property
    def last_netvol(self):
        return self.last_bar.netvol

    @last_open.setter
    def last_open(self, value):
        self.last_bar.open = value

    @last_close.setter
    def last_close(self, value):
        self.last_bar.close = value

    @last_high.setter
    def last_high(self, value):
        self.last_bar.high = value

    @last_low.setter
    def last_low(self, value):
        self.last_bar.low = value

    @last_volume.setter
    def last_volume(self, value):
        self.last_bar.volume = value

    @last_netvol.setter
    def last_netvol(self, value):
        self.last_bar.volume = value

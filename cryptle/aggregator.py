import logging
from cryptle.metric.base import Candle
from cryptle.event import source, on, Bus

logger = logging.getLogger(__name__)


class DecoratedAggregator:
    """ A wrapper for the actual aggregator implementation. Contains decorated
    aggergator functions for decoupling implementation of aggregator from the use of
    Event bus.

    Arg
    ---
    period: int
        The number of seconds for a candle bar to span
    auto_prune: boolean
        Option to prune the caching by this class
    maxsize: int
        Number of bars to be stored if choosing auto_prune

    """

    def __init__(self, period, auto_prune=True, maxsize=100):
        self.period = period
        self.aggregator = Aggregator(period, auto_prune, maxsize)

    @on('tick')
    def pushTick(self, data):
        for bar in self.aggregator.pushTick(data):
            if bar is None:
                logger.debug('No candle pushed for the first bar')
            else:
                self._emitAllMetrics(*bar)
                self._emitAggregatedCandle(bar)

    @on('candle')
    def pushCandle(self, bar):
        candle = self.aggregator.pushCandle(bar)
        self._emitAllMetrics(*bar)
        self._emitFullCandle(candle)

    @source('aggregator:new_candle')
    def _emitAggregatedCandle(self, bar):
        return bar

    @source('aggregator:new_candle')
    def _emitFullCandle(self, candle):
        return candle

    def _emitAllMetrics(self, o, c, h, l, t, v, nv):
        self._pushOpen(o)
        self._pushClose(c)
        self._pushHigh(h)
        self._pushLow(l)
        self._pushVolume(v)
        self._pushNetVolume(nv)
        self._pushTime(t)

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

    def last_open(self):
        return self.aggregator.last_open


class Aggregator:
    """Implementation of the generic candle aggregator.

    Aggregator is a class that converts tick values of either prices or Timeseries
    values to candle bar representation. It contains a subset of the functions of the
    CandleBar class in candle.py as it handles the aggregation of tick data to bar
    representation. This class is also an extension of the original CandleBar as it is
    designed to handle any tick-based value upon suitable wiring of interfaces. This
    class could also accept bar representation of data.

    Args
    ---
    period      : int
        The number of seconds for a candle bar to span
    auto_prune  : boolean
        Option to prune the caching by this class
    maxsize     : int
        Number of bars to be stored if choosing auto_prune

    """

    def __init__(self, period, auto_prune=True, maxsize=100):
        self.period = period
        self._bars = []  # this construct might be unnecessary
        self._auto_prune = auto_prune
        self._maxsize = maxsize
        self.last_timestamp = None

    def pushTick(self, data):
        """Generator function that provides public interface for accepting ticks.

        Args
        ---
        data    : list
            list-based representation of a tick data in [value, volume, timestamp, action]

        Note: To receive the outputs of this function, please loop through the generator
        function returned.

        """
        if len(data) == 4:
            value, timestamp, volume, action = data
        else:
            raise NotImplementedError('Please input a tick of correct format.')

        self.last_timestamp = timestamp

        # Initialize the candle collection
        if self.last_bar is None:
            yield self._pushInitCandle(value, timestamp, volume, action)

        # If tick arrived before next bar, update current candle
        if self._is_updated(timestamp):
            self.last_low = min(self.last_low, value)
            self.last_high = max(self.last_high, value)
            self.last_close = value
            self.last_volume += volume
            self.last_netvol += volume * action

        # If there is no tick arriving for the bars, yield empty bars
        else:
            while not self._is_updated(timestamp - self.period):
                yield self._pushEmptyCandle(
                    self.last_close, self.last_bar_timestamp + self.period
                )
                logger.debug('Pushed candle with timestamp {}', self.last_bar_timestamp)

            yield self._pushInitCandle(value, timestamp, volume, action)

    def pushPartialCandle(self, partial_bar):
        if len(partial_bar) == 7:
            o, c, h, l, ts, v, nv = partial_bar
        else:
            return NotImplementedError

        self.last_timestamp = ts

        # Initialise the candle collection
        if self.last_bar is None:
            logger.debug(f'Pushed the first candle {partial_bar}')
            yield self._pushPartialInitCandle(partial_bar)

        # If partial bar arrived before next bar, update current candle
        if self._is_updated(ts):
            self.last_low = min(self.last_low, l)
            self.last_high = max(self.last_high, h)
            self.last_close = c
            self.last_volume += v
            self.last_netvol += nv

        else:
            while not self._is_updated(ts - self.period):
                yield self._pushEmptyCandle(
                    self.last_close, self.last_bar_timestamp + self.period
                )
                logger.debug(f'Pushed candle with timestamp {self.last_bar_timestamp}')

            yield self._pushPartialInitCandle(partial_bar)

    def _pushPartialInitCandle(self, partial_bar):
        o, c, h, l, ts, v, nv = partial_bar

        round_ts = ts - ts % self.period
        new_candle = Candle(*partial_bar)
        self._bars.append(new_candle)

        if len(self._bars) > 1:
            finished_candle = self._bars[-2]
            return finished_candle._bar

    def _is_updated(self, timestamp):
        return timestamp < self.last_bar_timestamp + self.period

    def _is_due(self, timestamp):
        return timestamp > self.last_bar_timestamp + self.period

    def _prune(self, size):
        try:
            self._bars = self._bars[-size:]
        except IndexError:
            raise "Empty CandleBar cannot be pruned"

    def pushCandle(self, bar):
        """Provides public interface for accepting aggregated candles.

        Args
        ---
        bar     : Candle
            A Candle object

        """
        return self._pushFullCandle(*bar)
        # methods that output corresponding events to message bus

    def _pushInitCandle(self, value, timestamp, volume, action):
        round_ts = timestamp - timestamp % self.period
        new_candle = Candle(
            value, value, value, value, round_ts, volume, volume * action
        )
        self._bars.append(new_candle)
        if self._auto_prune:
            self._prune(self._maxsize)

        if len(self._bars) > 1:
            finished_candle = self._bars[-2]
            logger.debug(f'Pushed finished candle {finished_candle}.')
            return finished_candle._bar

    def _emitEvents(self, candle):
        self.bus.emit(f'aggregator:new_open', candle.open)
        self.bus.emit(f'aggregator:new_close', candle.close)
        self.bus.emit(f'aggregator:new_high', candle.high)
        self.bus.emit(f'aggregator:new_low', candle.low)
        self.bus.emit(f'aggregator:new_volume', candle.volume)
        self.bus.emit(f'aggregator:new_net_volume', candle.netvol)
        self.bus.emit(f'aggregator:new_timesatmp', candle.timestamp)

        self.bus.emit(f'aggregator:new_candle', candle._bar)

    def _pushFullCandle(self, o, c, h, l, t, v, nv):
        t = t - t % self.period
        full_candle = Candle(o, c, h, l, t, v, nv)
        self._bars.append(full_candle)
        if self._auto_prune:
            self._prune(self._maxsize)

        logger.debug(f'Pushed full candle {full_candle}.')
        return full_candle._bar

    def _pushEmptyCandle(self, value, timestamp):
        round_ts = timestamp - timestamp % self.period
        empty_candle = Candle(value, value, value, value, round_ts, 0, 0)
        self._bars.append(empty_candle)
        if self._auto_prune:
            self._prune(self._maxsize)
        logger.debug(f'Pushed empty candle with timestamp {timestamp}')

        if len(self._bars) > 1:
            finished_candle = self._bars[-2]
            logger.debug(f'Returning the second last candle')
            return finished_candle._bar

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

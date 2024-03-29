from .base import Metric, Candle
from .generic import *

import numpy as np


class CandleBar:
    """Container for candlesticks of a given length.

    Candle dependent metrics can be attached to a CandleBuffer instance. These
    metrics will then be pinged everytime a new candle is added to the buffer.
    Metrics must implement a ping() function which retrieves the newest candle
    from the buffer and update themselves accordingly.

    Args:
        period (int): Length of each candlestick of this collection.
        maxsize (int): Maximum number of historic candles to keep around.
        auto_prune (int): Flag for auto-removal of histoic candles.

    Attributes:
        period (int): Length in seconds of each candlestick.
        _bars (list): List of all the Candle objects.
        _metrics (list): Metrics that are attached to the CandleBar instance.
        _auto_prune (bool): Flag for auto-removal of historic candles.
        _maxsize (int): Maximum number of historic candles to keep around.
            Ignored if auto_prune is False.

    Note:
        New changes for automatic adding of empty candles might decrease
        stability of some candlemetrics
    """

    def __init__(self, period, auto_prune=False, maxsize=500):
        self.period = period
        self._bars = []
        self._metrics = []
        self._auto_prune = auto_prune
        self._maxsize = maxsize
        self.last_timestamp = None

    def pushTick(self, price, timestamp, volume=0, action=0):
        """Provides public interface for accepting ticks."""

        self.last_timestamp = timestamp

        # initialise the candle collection
        if self.last_bar is None:
            self._pushInitCandle(price, timestamp, volume, action)
            return

        # if tick arrived before next bar, update current candle
        if self._is_updated(timestamp):
            self.last_low = min(self.last_low, price)
            self.last_high = max(self.last_high, price)
            self.last_close = price
            self.last_volume += volume
            self.last_netvol += volume * action

        # if no tick arrived in between, append previous empty candles
        else:
            while not self._is_updated(timestamp - self.period):
                self._pushEmptyCandle(
                    self.last_close, self.last_bar_timestamp + self.period
                )
            self._pushInitCandle(price, timestamp, volume, action)

        # No one uses it yet so removed for reducing overhead
        # self._broadcastTick(price, timestamp, volume, action)
        # if self._auto_prune:
        #    self.prune(self._maxsize)

    def pushCandle(self, o, c, h, l, t, v, nv):
        """Provides public interface for accepting aggregated candles."""
        self._pushFullCandle(o, c, h, l, t, v, nv)

    def ping(self, timestamp):
        if self.last_bar is None:
            return
        while not self._is_updated(timestamp - self.period):
            self._pushEmptyCandle(
                self.last_close, self.last_bar_timestamp + self.period
            )

    def attach(self, metric):
        """Allow a candlemetric to subscribe for updates of candles."""
        self._metrics.append(metric)

    def prune(self, size):
        try:
            self._bars = self._bars[-size:]
        except IndexError:
            raise ("Empty CandleBar cannot be pruned")

    def open_prices(self, num_candles):
        return [x.open for x in self[-num_candles:]]

    def close_prices(self, num_candles):
        return [x.close for x in self[-num_candles:]]

    def _is_updated(self, timestamp):
        return timestamp < self.last_bar_timestamp + self.period

    def _pushFullCandle(self, o, c, h, l, t, v, nv):
        t = t - t % self.period
        self._bars.append(Candle(o, c, h, l, t, v, nv))
        self._broadcastCandle()

    def _pushInitCandle(self, price, timestamp, volume, action):
        round_ts = timestamp - timestamp % self.period
        self._bars.append(
            Candle(price, price, price, price, round_ts, volume, volume * action)
        )
        self._broadcastCandle()

    def _pushEmptyCandle(self, price, timestamp):
        round_ts = timestamp - timestamp % self.period
        self._bars.append(Candle(price, price, price, price, round_ts, 0, 0))
        self._broadcastCandle()

    def _broadcastCandle(self):
        for metric in self._metrics:
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

    # Sequence overloads
    def __len__(self,):
        return len(self._bars)

    def __getitem__(self, item):
        return self._bars[item]

    # Getters
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

    # Setters
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
        self._bars[-1].netvol = value


class CandleMetric(Metric):
    """Base class for candle dependent metrics.

    Metrics which are derived from an underlying candlestick chart should
    inherit from this class. Implementation of CandleMetric must call the parent
    constructor and pass an instance of CandleBar in their own constructors.

    Implementation class should also at least implement one of:
        - onCandle()
        - onTick(price, timestamp, volume, action)
    such that the metrics can properly subscribe to updates from the CandleBar.

    Example:
        def onCandle(self):
            pass

        def onTick(self, price, ts, volume, action):
            pass
    """

    def __init__(self, candle):
        self.candle = candle
        self.value = 0
        candle.attach(self)


class SMA(CandleMetric):
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
        raise NotImplementedError  # Not yet implemented


class WMA(CandleMetric):
    def __init__(self, candle, lookback, use_open=True, weights=None):
        super().__init__(candle)
        self._use_open = use_open
        self._lookback = lookback
        self._weights = weights or [
            2 * (i + 1) / (lookback * (lookback + 1)) for i in range(lookback)
        ]

    def onCandle(self):
        if len(self.candle) < self._lookback:
            return
        if self._use_open:
            prices = self.candle.open_prices(self._lookback)
        else:
            prices = self.candle.close_prices(self._lookback)
        self.value = np.average(prices, axis=0, weights=self._weights)

    def onTick(self, price, ts, volume, action):
        raise NotImplementedError  # Not yet implemented


class EMA(CandleMetric):
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
        raise NotImplementedError  # Not yet implemented


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
        raise NotImplementedError  # Not yet implemented


class MACD(CandleMetric):
    """Calculate and store the latest MACD value for the attached candle.

    The value of self.value (inherited from Metric) is set to be the difference
    between the difference of two moving averages and the moving average of this
    difference.

    Value:
        difference - MA of difference

    Args:
        fast (CandleMetric): Instance of moving average with shorter lookback.
        slow (CandleMetric): Instance of moving average with longer lookback.
        lookback (int): Number of bars to consider for the difference moving average.
        weights (list): Weighting to average the MA difference. Defaults to linear.

    Attributes:
        diff (float):
    """

    def __init__(self, fast, slow, lookback, weights=None):
        assert fast.candle == slow.candle  # @Use proper error
        super().__init__(fast.candle)
        self._fast = fast
        self._slow = slow
        self._lookback = lookback
        self._weights = weights or [
            2 * (i + 1) / (lookback * (lookback + 1)) for i in range(lookback)
        ]
        self._past = []

    def onCandle(self):
        self.diff = self._fast - self._slow
        self._past.append(self.diff)
        self._past = self._past[-self._lookback :]
        self.diff_ma = 0

        if len(self._past) == self._lookback:
            self.diff_ma = np.average(self._past, axis=0, weights=self._weights)
            self.value = self.diff - self.diff_ma

    def onTick(self, price, ts, volume, action):
        raise NotImplementedError  # Not yet implemented


# Review its role and duplication in metric/generic.py
class Difference(CandleMetric):
    """Difference.

    This class computes a dictionary of lists of historic n-th differences.

    This class supports differencing of multiple attributes of a class. In default settings, no
    additional argument is needed. Only the 'value' attribute of the Metric class would be
    differencd. For any additional attributes required differencing, the string of the required
    attribute names should be parsed during the construction of this Difference class.

    The class returns a dictionary of lists, with the key being the names of differenced attributes.
    Resuls up to the specified lookback period would be stored and returned.

    Value:
        The last value of the n-th difference of the series

    Args:
        n         (int): The n-th order difference required.
        lookback  (int): Number of results to be stored
        *args     (str): Strings of names of attributes of the Metric parsed for differencing

    Attributes:
        output   (list): The n-th times difference of the required attributes (value + **kwargs)
        value   (float): The latest value of output['value'][-1]
    """

    def __init__(
        self,
        metric,
        *args,
        n=1,
        lookback=4  # not yet implemented, 4 as default for future DIDO scaling
    ):

        super().__init__(metric.candle)
        self._metric = metric
        self._lookback = lookback
        self._n = n
        self._attrs = list(args)  # addtional string arguments to diff attributes
        self._record = {"value": []}  # dictionary of lists storing raw attr values
        self.output = {}  # dictonary of lists storing differenced attributes
        self.value = 0

        if len(self._attrs) > 0:
            # create return values and indexing attribute to record
            for attr in self._attrs:
                self.__dict__[attr] = 0
                self._record[attr] = []

    def onCandle(self):
        if len(self.candle) < self._n:
            return
        # append the updated attriute value to record
        self._record["value"].append(float(self._metric))
        for attr in self._attrs:
            self._record[attr].append(self._metric.__dict__[attr])
        # differencing all record in self._records using np.diff method
        for attr, record in self._record.items():
            self.output[attr] = np.diff(record, self._n)
        # assigning proper return values for access
        if len(self.output["value"]) > 0:
            self.value = self.output["value"][-1]
            for attr in self._attrs:
                self.__dict__[attr] = self.output[attr][-1]

    def onTick(self):
        raise NotImplementedError  # not yet implemented


class BollingerBand(CandleMetric):
    """Bollinger band.

    Value:
        Band percentage difference.

    Args:
        lookback (int): Number of bars to consider.
        use_open (bool): Flag for using open/close price.
        sd (float): Standard deviations. Can be override by upper_sd/lower_sd.
        upper_sd (float): Upper band standard deviation.
        lower_sd (float): Lower band standard deviation.

    Attributes:
        width: Volatility of recent candles.
        upperband: Price at top of the bollinger band.
        lowerband: Price at bottom of the bollinger band.
        band: Percent difference between top and bottom band.
    """

    def __init__(
        self, candle, lookback, use_open=True, sd=2, upper_sd=None, lower_sd=None
    ):

        super().__init__(candle)
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
        self.upperband = prices[-1] + self._upper_sd * self.width
        self.lowerband = prices[-1] - self._lower_sd * self.width
        self.band = ((self.upperband / self.lowerband) - 1) * 100
        self.value = self.band

    def onTick(self, price, ts, volume, action):
        raise NotImplementedError  # Not yet implemented


class MABollinger(CandleMetric):
    """Moving average impose on bollinger band.

    Args:
        bband (BollingerBand): Underlying bollinger band
        lookback (int): Lookback of the moving average
        weights (list): Weighting for averaging. Defaults to None (simple average).
    """

    def __init__(self, bband, lookback, use_open=True, weights=None):

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
            self.value = np.mean(self._bands[-self._lookback :])
        else:
            self.value = np.average(self._weights, axis=0, weights=self._weights)

    def onTick(self, price, ts, volume, action):
        raise NotImplementedError  # Not yet implemented


class RSI(CandleMetric):
    """Calculate and store the latest RSI value for the attached candle"""

    def __init__(self, candle, lookback, use_open=True):
        super().__init__(candle)
        self._use_open = use_open
        self._lookback = lookback
        self._weight = 1 / lookback  # MODIFIED to suit our purpose
        self.up = []
        self.down = []
        self.ema_up = None
        self.ema_down = None

    def onCandle(self):
        if len(self.candle) < 2:
            return

        if self._use_open:
            if self.candle.last_open > self.candle[-2].open:
                self.up.append(abs(self.candle.last_open - self.candle[-2].open))
                self.down.append(0)
            else:
                self.down.append(abs(self.candle[-2].open - self.candle.last_open))
                self.up.append(0)
        else:
            if self.candle.last_close > self.candle[-2].close:
                self.up.append(abs(self.candle.last_close - self.candle[-2].close))
                self.down.append(0)
            else:
                self.down.append(abs(self.candle[-2].close - self.candle.last_close))
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
                self.value = 100 - 100 / (1 + self.ema_up / self.ema_down)
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
            self.value = 100 - 100 / (1 + self.ema_up / self.ema_down)
        except ZeroDivisionError:
            if self.ema_down == 0 and self.ema_up != 0:
                self.value = 100
            elif self.ema_up == 0 and self.ema_down != 0:
                self.value = 0
            elif self.ema_up == 0 and self.ema_down == 0:
                self.value = 50

    def onTick(self, price, ts, volume, action):
        raise NotImplementedError  # Not yet implemented

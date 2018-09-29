from metric.base import Timeseries
import numpy as np

class BollingerBand(Timeseries):
    def __init__(self, ts, lookback, sd=2, upper_sd = None, lower_sd = None):
        if upper_sd is None:
            upper_sd = sd
        if lower_sd is None:
            lower_sd = sd

        self._lookback  = lookback
        self._width     = width(ts, lookback)
        self._upperband = upperband(ts, lookback, upper_sd)
        self._lowerband = lowerband(ts, lookback, lower_sd)
        self._band      = band(ts, lookback, upper_sd, lower_sd)
        self._value     = None

    def onCandle(self):
        self._value = float(self._band)

    def onTick(self, price, timestamp, volume, action):
        raise NotImplementedError

class width(Timeseries):
    def __init__(self, ts, lookback):
        self._lookback = lookback
        self._ts       = ts
        self._cache    = []
        self.value     = None

    @on('aggregator:new_candle')
    @Timeseries.cache
    def onCandle(self):
        self.value = np.std(self._cache)

    def onTick(self, price, timestamp, volume, action):
        raise NotImplementedError

class upperband(Timeseries):
    def __init__(self, ts, lookback, upper_sd):
        self._lookback = lookback
        self._ts       = ts
        self._cache    = []
        self._width    = width(ts, lookback)
        self._uppersd  = upper_sd
        self.value     = None

    @on('aggregator:new_candle')
    @Timeseries.cache
    def onCandle(self):
        self.value = self._cache[-1] + self._upper_sd * self._width

    def onTick(self, price, timestamp, volume, action):
        raise NotImplementedError


class lowerband(Timeseries):
    def __init__(self, ts, lookback, lower_sd):
        self._lookback = lookback
        self._ts       = ts
        self._cache    = []
        self._width    = width(ts, lookback)
        self._lowersd  = lower_sd
        self.value     = None

    @on('aggregator:new_candle')
    @Timeseries.cache
    def onCandle(self):
        self.value = self._cache[-1] + self._lower_sd * self._width

    def onTick(self, price, timestamp, volume, action):
        raise NotImplementedError

class band(Timeseries):
    def __init__(self, ts, lookback, upper_sd, lower_sd):
        self._lookback = lookback
        self._ts       = ts
        self._upperband = upperband(ts, lookback, upper_sd)
        self._lowerband = lowerband(ts, lookback, lower_sd)

    def onCandle(self):
        self.value = ((self._upperband / self._lowerband) - 1) * 100

    def onTick(self, price, timestamp, volume, action):
        raise NotImplementedError



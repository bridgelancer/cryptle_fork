from metric.base import Timeseries
from cryptle.event import on, source
import numpy as np

class BollingerBand(Timeseries):
    def __init__(self, ts, lookback, sd=2, name=None, upper_sd=None, lower_sd=None):
        super().__init__(ts=ts, name=name)
        if upper_sd is None:
            upper_sd = sd
        if lower_sd is None:
            lower_sd = sd

        self._ts        = ts
        self._cache     = []
        self._lookback  = lookback
        self._width     = width(ts, lookback)
        self._upperband = upperband(ts, lookback, self._width, upper_sd)
        self._lowerband = lowerband(ts, lookback, self._width, lower_sd)
        self.value     = None
        self.x = 0

    def evaluate(self):
        try:
            self.value = (float(self._upperband) / float(self._lowerband) - 1) * 100
        except:
            pass

    def onTick(self, price, timestamp, volume, action):
        raise NotImplementedError

class width(Timeseries):
    def __init__(self, ts, lookback, name=None):
        super().__init__(ts=ts, name=name)
        self._lookback = lookback
        self._ts       = ts
        self._cache    = []
        self.value     = None

    @Timeseries.cache
    def evaluate(self):
        self.value = np.std(self._cache, ddof=1)
        self.broadcast()

    def onTick(self, price, timestamp, volume, action):
        raise NotImplementedError

class upperband(Timeseries):
    def __init__(self, ts, lookback, width, upper_sd, name=None):
        super().__init__(ts=ts, name=name)
        self._lookback = lookback
        self._ts       = ts
        self._cache    = []
        self._width    = width
        self._uppersd  = upper_sd
        self.value     = None

    @Timeseries.cache
    def evaluate(self):
        self.value = sum(self._cache)/self._lookback + self._uppersd * float(self._width)
        self.broadcast()

    def onTick(self, price, timestamp, volume, action):
        raise NotImplementedError


class lowerband(Timeseries):
    def __init__(self, ts, lookback, width, lower_sd, name=None):
        super().__init__(ts=ts, name=name)
        self._lookback = lookback
        self._ts       = ts
        self._cache    = []
        self._width    = width
        self._lowersd  = lower_sd
        self.value     = None

    @Timeseries.cache
    def evaluate(self):
        self.value = sum(self._cache)/self._lookback - self._lowersd * float(self._width)
        self.broadcast()

    def onTick(self, price, timestamp, volume, action):
        raise NotImplementedError

#class band(Timeseries):
#    def __init__(self, ts, lookback, upper_sd, lower_sd):
#        self._lookback = lookback
#        self._ts       = ts
#        self._upperband = upperband(ts, lookback, upper_sd)
#        self._lowerband = lowerband(ts, lookback, lower_sd)
#
#    def evaluate(self):
#        self.value = ((float(self._upperband) / float(self._lowerband)) - 1) * 100
#
#    def onTick(self, price, timestamp, volume, action):
#        raise NotImplementedError



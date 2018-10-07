from metric.base import Timeseries
from metric.timeseries.wma import WMA
from cryptle.event import on

import numpy as np


def default(lookback):
    return [2 * (i + 1) / (lookback * (lookback + 1)) for i in range(lookback)]

# how to solve the problem of two updates arising from two timeseries?
class MACD(Timeseries):
    # MACD takes two timeseries. The two timeseries should update concurrently in order for a valid
    # value produed
    def __init__(self, fast, slow, lookback, name=None, weights=default):
        # need some way to work around metrics that require multiple timeseries
        self._ts       = [fast, slow]
        super().__init__(ts=self._ts, name=name)
        self._fast     = fast
        self._slow     = slow
        self._lookback = lookback
        self._weights  = weights(lookback)

        self.diff      = diff(self._fast, self._slow)
        self.diff_ma   = diff_ma(self.diff, lookback, self._weights)
        self.value = None

    def evaluate(self):
        self.broadcast()
        try:
            self.value = float(self.diff) - float(self.diff_ma)
        except:
            pass

    def onTick(self, price, timestamp, volume, action):
        raise NotImplementedError

class diff(Timeseries):
    def __init__(self, fast, slow, name=None):
        self._ts = [fast, slow]
        super().__init__(ts=self._ts, name=name)
        self._cache = []
        self._fast = fast
        self._slow = slow
        self._lookback = 2
        self.value = None

    @Timeseries.cache
    def evaluate(self):
        try:
            self.value = float(self._fast) - float(self._slow)
        except:
            pass
        self.broadcast()

    def onTick(self, price, timestamp, volume, action):
        raise NotImplementedError

class diff_ma(Timeseries):
    def __init__(self, ts, lookback, weights, name=None):
        self._ts       = ts
        super().__init__(ts=self._ts, name=name)
        self._lookback = lookback
        self._cache    = []
        self._weights  = weights
        self.value     = None

    @Timeseries.cache
    def evaluate(self):
        try:
            self.value = np.average(self._cache, axis=0, weights = self._weights)
        except:
            pass
        self.broadcast()


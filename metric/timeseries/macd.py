from metric.base import Timeseries
from metric.timeseries.wma import WMA
from cryptle.event import on

import numpy as np


def default(lookback):
    return [2 * (i + 1) / (lookback * (lookback + 1)) for i in range(lookback)]

class MACD(Timeseries):
    def __init__(self, fast, slow, lookback, weights=default):
        self._fast     = fast
        self._slow     = slow
        self._lookback = lookback
        self._weights  = weights(lookback)

        self.diff      = diff(self._fast, self._slow)
        self.diff_ma   = diff_ma(lookback, self._weights)
        self.value = None

    def onCandle(self):
        self.diff.onCandle()
        self.diff_ma.onCandle()
        try:
            self.value = float(self.diff) - float(self.diff_ma)
        except:
            pass

    def onTick(self, price, timestamp, volume, action):
        raise NotImplementedError

class diff(Timeseries):
    def __init__(self, fast, slow):
        self._fast = fast
        self._slow = slow
        self.value = None

    @on('aggregator:new_candle')
    def onCandle(self):
        try:
            self.value = float(self._fast) - float(self._slow)
        except:
            pass

    def onTick(self, price, timestamp, volume, action):
        raise NotImplementedError

# review this class, probably using Timeseries.cache
class diff_ma(Timeseries):
    def __init__(self, lookback, diff, weights):
        self._lookback = lookback
        self._cache    = []
        self._ts       = diff
        self._weights  = weights
        self.value     = None

    @Timeseries.cache
    def onCandle(self):
       self.value = np.average(self._cache, axis=0, weights = self._weights)


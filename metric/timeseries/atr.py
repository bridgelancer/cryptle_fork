from metric.base import Timeseries
from cryptle.event import source, on
import numpy as np

class ATR(Timeseries):

    def __init__(self, candle, lookback):
        self._lookback = lookback
        self._candle   = candle
        self.value     = None
        self._tr       = true_range(lookback, candle) # tr is the true_range object to be passed into the "ATR" wrapper

    def onCandle(self):
        self.value = (self.value * (self._lookback -1) * self._tr) / self._lookback
        self._tr.onCandle()

    def onTick(self, price, ts, volume, action):
        raise NotImplementedError

class true_range(Timeseries):
    def __init__(self, lookback, candle):
        self.value     = None
        self._lookback = lookback
        self._ts       = candle     # misnomer to fit the decorator usage
        self._cache    = []

    @on('aggregator:new_candle')
    @Timeseries.cache
    def onCandle(self):
        if self.value is None and len(self._cache) == self._lookback:
            self.value = np.mean(self._cache)
        else:
            t1 = self._cache[-2].high - self._cache[-2].low
            t2 = abs(self._cache[-2].high - self._cache[-3].close)
            t3 = abs(self._cache[-2].low - self._cache[-3].close)
            self.value = max(t1, t2, t3)

    def onTick(self, price, ts, volume, action):
        raise NotImplementedError


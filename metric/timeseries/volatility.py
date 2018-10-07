from metric.base import Timeseries
from cryptle.event import on, source
import numpy as np

class Volatility(Timeseries):
    def __init__(self, ts, lookback):
        self._lookback = lookback
        self._ts       = ts
        self._cache    = []

    @Timeseries.cache
    def evaluate(self, bar, candle):
        if np.std(self._cache) > 0:
            self.value = 1 / np.std(self._cache, ddof=1)
        else:
            self.value = 100

    def onTick(self, price, timestamp, volume, action):
        raise NotImplementedError


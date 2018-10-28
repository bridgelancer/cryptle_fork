from metric.base import Timeseries
import scipy.stats as sp

class Skewness(Timeseries):
    def __init__(self, ts, lookback, name=None):
        super().__init__(ts=ts)
        self._lookback = lookback
        self._ts       = ts
        self._cache    = []

    @Timeseries.cache
    def evaluate(self):
        self.value = sp.skew(self._cache, bias=False)
        self.broadcast()

    def onTick(self, price, timestamp, volume, action):
        raise NotImplementedError



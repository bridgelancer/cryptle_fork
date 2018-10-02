from metric.base import Timeseries
from cryptle.event import on, source
import scipy.stats as sp

class Skewness(Timeseries):
    def __init__(self, ts, lookback):
        self._lookback = lookback
        self._ts       = ts
        self._cache    = []

    @on('aggregator:new_candle')
    @Timeseries.cache
    def evaluate(self):
        self.value = sp.skew(self._cache)

    def onTick(self, price, timestamp, volume, action):
        raise NotImplementedError



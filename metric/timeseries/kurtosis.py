from cryptle.event import on
from metric.base import Timeseries
import numpy as np

class Kurtosis(Timeseries):
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

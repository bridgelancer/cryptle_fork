from cryptle.event import on
from metric.base import Timeseries
import numpy as np

class Difference(Timeseries):
    def __init__(self, ts, n=1):
        self._ts    = ts
        self._cache = []
        self._n     = n
        self.value  = None

    @on('aggregator:new_candle')
    @Timeseries.cache
    def onCandle(self):

        if len(self._cache) == self._n:
            output = np.diff(self._cache, self._n)
            self.value = output[-1]

    def onTick(self):
        raise NotImplementedError



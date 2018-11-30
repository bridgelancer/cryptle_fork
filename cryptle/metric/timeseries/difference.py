from cryptle.metric.base import Timeseries
import numpy as np

class Difference(Timeseries):
    def __init__(self, ts, n=1, name=None):
        super().__init__(ts=ts)
        self._ts    = ts
        self._cache = []
        self._n     = n
        self._lookback = self._n + 1
        self.value  = None

    @Timeseries.cache
    def evaluate(self):
        if len(self._cache) == self._lookback:
            output = np.diff(self._cache, self._n)
            self.value = output[-1]
            self.broadcast()

    def onTick(self):
        raise NotImplementedError

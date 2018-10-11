from metric.base import Timeseries
import numpy as np

class SD(Timeseries):
    def __init__(self, ts, lookback, name=None):
        super().__init__(ts=ts, name=name)
        self._lookback = lookback
        self._ts       = ts
        self.value     = 0
        self._cache   = []

    @Timeseries.cache
    def evaluate(self):
        calc = self._cache[:]
        if np.std(calc) > 0.001 * np.average(calc): # SHOULD SET TO A FRACTION OF THE MEAN VALUE OF THE SERIES
            self.value = 1 / np.std(calc, ddof=1)
        else:
            self.value = (float(self._ts) - np.average(calc)) / 0.001 * np.average(calc)
        self.broadcast()

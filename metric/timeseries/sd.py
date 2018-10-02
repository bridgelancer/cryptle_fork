from metric.base import Timeseries
from cryptle.event import on, source
import numpy as np

class SD(Timeseries):
    def __init__(self, ts, lookback):
        self._lookback = lookback
        self._ts       = ts
        self.value     = 0
        self._record   = []

    @on('aggregator:candle')
    @Timeseries.cache
    def evaluate(self):
        calc = self._record[:-1]
        if np.std(calc) > 0.001 * np.average(calc): # SHOULD SET TO A FRACTION OF THE MEAN VALUE OF THE SERIES
            self.value = (float(self._ts) - np.average(calc)) / np.std(calc)
        else:
            self.value = (float(self._metric) - np.average(calc)) / 0.001 * np.average(calc)

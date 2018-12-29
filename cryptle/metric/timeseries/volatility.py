from cryptle.metric.base import Timeseries
import numpy as np


class Volatility(Timeseries):
    """Timeseries that calculate the value of the 1/standard deviation of the sampled data

    Args
    ----
    lookback : int
        The lookback period for sampling and calculating the 1/sd.

    """

    def __init__(self, ts, lookback):
        self._lookback = lookback
        self._ts = ts
        self._cache = []

    @Timeseries.cache('normal')
    def evaluate(self, bar, candle):
        if np.std(self._cache) > 0:
            self.value = 1 / np.std(self._cache, ddof=1)
        else:
            self.value = 100

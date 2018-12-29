from cryptle.metric.base import Timeseries
import numpy as np


class SD(Timeseries):
    """Timeseries to calculate the value of standard deviation of upstream.

    Args
    ---
    lookback : int
        The lookback period for sampling and calculating the standard deviation.

    """

    def __init__(self, ts, lookback, name=None):
        super().__init__(ts)
        self._lookback = lookback
        self._ts = ts
        self.value = 0
        self._cache = []

    @Timeseries.cache('normal')
    def evaluate(self):
        calc = self._cache[:]
        if np.std(calc) > 0.001 * np.average(
            calc
        ):  # SHOULD SET TO A FRACTION OF THE MEAN VALUE OF THE SERIES
            self.value = 1 / np.std(calc, ddof=1)
        else:
            self.value = (float(self._ts) - np.average(calc)) / 0.001 * np.average(calc)
        self.broadcast()

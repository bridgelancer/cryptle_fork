from cryptle.metric.base import Timeseries
import numpy as np


class WMA(Timeseries):
    # Todo May be better to use a function just like EMA instead
    def __init__(self, ts, lookback, name="wma", weights=None, bar=False):
        """Timeseries for calcuing the weighted moving average of upstream.

        Args
        ----
        lookback : int
            The lookback period for sampling and calculating the WMA.
        weights: list, optional
            A list of weighting to weight the past historical values, default is None

        """

        super().__init__(ts)
        self._lookback = lookback
        self._weights = weights or [
            2 * (i + 1) / (lookback * (lookback + 1)) for i in range(lookback)
        ]
        self._ts = ts
        self._cache = []
        self.value = None
        self._bar = bar

    @Timeseries.cache('normal')
    def evaluate(self):
        if len(self._cache) == self._lookback:
            self.value = np.average(self._cache, axis=0, weights=self._weights)
        self.broadcast()

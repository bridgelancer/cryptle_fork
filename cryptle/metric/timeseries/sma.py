from cryptle.metric.base import Timeseries, Candle
import numpy as np


class SMA(Timeseries):
    def __init__(self, ts, lookback, name="sma", bar=False, list=False):
        """Timeseries for calculating the simple moving average of the upstream.

        Args
        ----
        lookback : The lookback period for calculating the SMA.

        """
        super().__init__(ts)
        self._lookback = lookback
        self._ts = ts
        self._cache = []
        self._bar = bar
        self.value = None
        if list:
            self.onList()

    # Any ts would call evaluate as new_candle emits. This updates its ts value for calculating the
    # correct value for output and further sourcing.
    @Timeseries.cache('normal')
    def evaluate(self, candle=None):
        self.value = np.mean(self._cache)
        self.broadcast()

    def onList(self):
        self.history = list(pd.DataFrame(self._ts).rolling(self._lookback).mean())

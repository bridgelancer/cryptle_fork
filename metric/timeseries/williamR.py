from metric.base import Timeseries
from cryptle.event import on, source
import numpy as np

class WilliamPercentR(Timeseries):
    def __init__(self, candle, lookback, name=None):
        self._ts       = [candle.c, candle.h, candle.l]
        super().__init__(ts=self._ts, name=name)
        self._lookback = lookback
        self._cache    = []
        self.value     = 0

    @Timeseries.cache
    def evaluate(self):
        if len(self._cache) >= self._lookback:
            # pending confirmation
            high_prices  = [x[1]   for x in self._cache[:-1]]
            low_prices   = [x[2]   for x in self._cache[:-1]]
            close_prices = [x[0]   for x in self._cache[:-1]]

            self.value = (max(high_prices) - self._cache[-1][0] ) / (max(high_prices) - min(low_prices)) * -100
            self.broadcast()

    def onTick(self, price, timestamp, volume, action):
        raise NotImplementedError


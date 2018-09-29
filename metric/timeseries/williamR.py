from metric.base import Timeseries
from metric.event import on, source
import numpy as np

class WilliamPercentR(Timeseries):
    def __init__(self, candle, lookback):
        self._lookback = lookback
        self._ts       = candle
        self._cache    = []
        self.value     = 0

    @on('aggregator:new_candle')
    @Timeseries.cache
    def onCandle(self):
        window = self._cache[-lookback-1:-1]
        # pending confirmation
        high_prices  = [x.high  for x in window]
        low_prices   = [x.low   for x in window]
        close_prices = [x.close for x in window]

        self.value = (max(high_prices) - self._cache[-1].close ) / (max(high_prices) - min(low_prices)) * -100

    def onTick(self, price, timestamp, volume, action):
        raise NotImplementedError


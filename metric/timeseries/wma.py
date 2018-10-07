from metric.base import Timeseries
from cryptle.event import on, source
import numpy as np

class WMA(Timeseries):

    def __init__(self, ts, lookback, name=None, weights=None, bar=False):
        super().__init__(ts=ts, name=name)
        self._lookback = lookback
        self._weights  = weights or [2 * (i+1) / (lookback * (lookback + 1)) for i in range(lookback)]
        self._ts    = ts
        self._cache = []
        self.value  = None
        self._bar    = bar

    @Timeseries.cache
    def evaluate(self):
        if len(self._cache) == self._lookback:
            self.value = np.average(self._cache, axis=0, weights=self._weights)

        @Timeseries.bar_cache
        def toBar(self, candle):
        #price candle wrapper was passed into this function for constructing candles
            if len(self.o) == self._lookback:
                o = np.average(self.o, axis=0, weights=self._weights)
                c = np.average(self.c, axis=0, weights=self._weights)
                h = np.average(self.h, axis=0, weights=self._weights)
                l = np.average(self.l, axis=0, weights=self._weights)

                self.bar = Candle(o, c, h, l, 0, 0)

        if self._bar:
            self.o = []
            self.c = []
            self.h = []
            self.l = []
            toBar(candle)
        self.broadcast()

    def onTick(self, price, ts, volume, action):
        raise NotImplementedError

from metric.base import Timeseries, Candle
from cryptle.event import on, source, Bus
import numpy as np

class SMA(Timeseries):

    def __init__(self, ts, lookback, name=None, bar=False, list=False):
        super().__init__(ts=ts, name=name)
        self._lookback = lookback
        self.name = name
        self._ts    = ts
        self._cache = []
        self._bar   = bar
        self.value  = None
        if list:
            self.onList()

    # Any ts would call onCandle as new_candle emits. This updates its ts value for calculating the
    # correct value for output and further sourcing.
    @Timeseries.cache
    def onCandle(self, candle=None):
        print(self._cache)
        self.value = np.mean(self._cache)

        @Timeseries.bar_cache
        def toBar(self, candle):
        # price candle wrapper was passed into this function for constructing candles
            if len(self.o) == self._lookback:
                o = np.mean(self.o)
                c = np.mean(self.c)
                h = np.mean(self.h)
                l = np.mean(self.l)

                self.bar = Candle(o, c, h, l, t, 0, 0)

        if self._bar:
            self.o = []
            self.c = []
            self.h = []
            self.l = []
            toBar(candle)
        self.broadcast()

    def onTick(self):
        raise NotImplementedError

    def onList(self):
        self.history = list(pd.DataFrame(self._ts).rolling(self._lookback).mean())

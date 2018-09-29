from metric.base import Timeseries, Candle
from cryptle.event import on, source
import numpy as np

class SMA(Timeseries):

    def __init__(self, ts, lookback, bar=False, list=False):
        self._lookback = lookback
        self._ts    = ts
        self._cache = []
        self._bar   = bar
        self.value  = None
        if list:
            self.onList()

    @on('aggregator:new_candle')
    @Timeseries.cache
    def onCandle(self, candle=None):
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

    def onTick(self):
        raise NotImplementedError

    def onList(self):
        self.history = list(pd.DataFrame(self._ts).rolling(self._lookback).mean())

from metric.base import Timeseries
from cryptle.event import on

def default(lookback):
    return 2 / (lookback + 1)

class EMA(Timeseries):
    def __init__(self, ts, lookback, weight=default, bar=False):
        self._lookback = lookback
        self._weight = weight(lookback) # weight is a math function that takes lookback as argument and returns a float in range (0, 1)
        self._ts     = ts
        self.value   = None
        self._bar    = bar

    @on('aggregator:new_candle')
    def evaluate(self, candle=None):

        if self.value is None:
            self.value = float(self._ts)
        else:
            self.value = float(self._ts) * self._weight + (1 - self._weight) * self.value

        def toBar(self, candle):
            # price candle wrapper was passed into this function for constructing candles
            if self.o is not None:
                self.o = float(candle.o)
                self.h = float(candle.h)
                self.c = float(candle.c)
                self.l = float(candle.l)
                self.t = float(candle.t)

                self.bar = Candle(o, c, h, l, t, 0, 0)
            else:
                self.o = float(candle.o) * self._weight + (1 - self._weight) * self.o
                self.c = float(candle.c) * self._weight + (1 - self._weight) * self.c
                self.h = float(candle.h) * self._weight + (1 - self._weight) * self.h
                self.l = float(candle.l) * self._weight + (1 - self._weight) * self.l

                self.bar = Candle(o, c, h, l, t, 0, 0)
        if self._bar:
            self.o = self.h = self.c = self.l = None
            toBar(candle)

    def onTick(self, value, timestamp, volume=0, netvol=0):
        raise NotImplementedError

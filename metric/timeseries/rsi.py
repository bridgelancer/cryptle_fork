from metric.base import Timeseries
from cryptle.event import on, source
import numpy as np

def default(lookback):
    return 1 / lookback

class RSI(Timeseries):
    def __init__(self, ts, lookback, name=None, weight=default):
        super().__init__(ts=ts, name=name)
        self._lookback = lookback
        self._ts       = ts
        self._cache    = []
        self._weight   = weight(lookback)
        self._up       = []
        self._down     = []
        self._ema_up   = None
        self._ema_down = None

    def evaluate(self):
        self._cache.append(float(self._ts))
        if len(self._cache) < 2:
            return
        if self._cache[-1] > self._cache[-2]:
            self._up.append(abs(self._cache[-1] - self._cache[-2]))
        else:
            self._down.append(abs(self._cache[-1] - self._cache[-2]))
        if len(self._up) < self._lookback or len(self._down) < self._lookback:
            return

        price_up   = self._up[-1]
        price_down = self._down[-1]

        if self._ema_up is None and self._ema_down is None:
            self._ema_up    = sum([x for x in self._up]) / len(self._up)
            self._ema_down  = sum([x for x in self._down]) / len(self._down)
            try:
                self.value = 100 - 100 / (1 + self._ema_up/self._ema_down)
            except ZeroDivisionError:
                if self._ema_down == 0 and self._ema_up != 0:
                    self.value = 100
                elif self._ema_up == 0 and self._ema_down != 0:
                    self.value = 0
                elif self._ema_up == 0 and self._ema_down == 0:
                    self.value = 50
            return

        self._ema_up   = self._weight * price_up + (1 - self._weight) * self._ema_up
        self._ema_down = self._weight * price_down + (1 - self._weight) * self._ema_down


        try:
            self.value = 100 - 100 / (1 + self._ema_up/self._ema_down)
        except ZeroDivisionError:
            if self._ema_down == 0 and self._ema_up != 0:
                self.value = 100
            elif self._ema_up == 0 and self._ema_down != 0:
                self.value = 0
            elif self._ema_up == 0 and self._ema_down == 0:
                self.value = 50

        if len(self._cache) > 2:
            self._cache = self._cache[-2:]

    def onTick(self, price, timestamp, volume, action):
        raise NotImplementedError


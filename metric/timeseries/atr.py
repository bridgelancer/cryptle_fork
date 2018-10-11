from metric.base import Timeseries
import numpy as np

class ATR(Timeseries):

    def __init__(self, candle, lookback, name=None):
        self._ts       = [candle.c, candle.h, candle.l]
        super().__init__(ts=self._ts, name=None)
        self._lookback = lookback
        self.value     = None
        self._tr       = true_range(lookback, self._ts) # tr is the true_range object to be passed into the "ATR" wrapper

    def evaluate(self):
        self.broadcast()
        try:
            if self.value is None:
                self.value = float(self._tr)
            else:
                self.value = (self.value * (self._lookback -1) + float(self._tr)) / self._lookback
        except:
            pass

    def onTick(self, price, ts, volume, action):
        raise NotImplementedError

class true_range(Timeseries):
    def __init__(self, lookback, ts):
        super().__init__(ts=ts, name=None)
        self.value     = None
        self._lookback = lookback
        self._ts       = ts
        self._cache    = []
        self.bar       = True

    @Timeseries.cache
    def evaluate(self):
        if len(self._cache) >= 3:
            last_close = self._cache[-3][0]
            high = self._cache[-2][1]
            low = self._cache[-2][2]

        if self.value is None and len(self._cache) == self._lookback:
            self.value = np.mean([x[1] for x in self._cache]) - np.mean([x[2] for x in
                self._cache])
        elif self.value is not None:
            t1 = float(high) - float(low)
            t2 = abs(float(high) - float(last_close))
            t3 = abs(float(low) - float(last_close))
            self.value = max(t1, t2, t3)
        self.broadcast()

    def onTick(self, price, ts, volume, action):
        raise NotImplementedError


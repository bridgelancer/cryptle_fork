from cryptle.metric.base import Timeseries, GenericTS
import numpy as np


class ATR(Timeseries):

    def __init__(self, candle, lookback, name=None):
        self._ts       = [candle.c, candle.h, candle.l]
        super().__init__(ts=self._ts)
        self._lookback = lookback
        self.value     = None

        def true_range(atr):
            if len(atr._cache) >= 3:
                last_close = atr._cache[-3][0]
                high = atr._cache[-2][1]
                low = atr._cache[-2][2]

            if atr.value is None and len(atr._cache) == atr._lookback:
                return np.mean([x[1] for x in atr._cache]) - np.mean([x[2] for x in
                    atr._cache])
            elif atr.value is not None:
                t1 = float(high) - float(low)
                t2 = abs(float(high) - float(last_close))
                t3 = abs(float(low) - float(last_close))
                return max(t1, t2, t3)

        self._tr       = GenericTS(self._ts, lookback=lookback, eval_func=true_range, args=[self]) # tr is the true_range object to be passed into the "ATR" wrapper

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

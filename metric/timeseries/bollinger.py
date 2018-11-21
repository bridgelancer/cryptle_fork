from metric.base import Timeseries, GenericTS
import numpy as np


class BollingerBand(Timeseries):
    def __init__(self, ts, lookback, sd=2, name=None, upper_sd=None, lower_sd=None):
        super().__init__(ts=ts)
        if upper_sd is None:
            self._uppersd = sd
        else:
            self._uppersd = upper_sd

        if lower_sd is None:
            self._lowersd = sd
        else:
            self._lowersd = lower_sd

        # eval_func for computing subseries
        def width(bb):
            return np.std(bb.width._cache, ddof=0)

        # eval_func for computing subseries
        def upperband(bb):
            return sum(bb.upperband._cache)/bb._lookback + bb._uppersd * float(bb.width)

        # eval_func for computing subseries
        def lowerband(bb):
            return sum(bb.lowerband._cache)/bb._lookback - bb._lowersd * float(bb.width)

        # A BollingerBand object holds these subseries
        self.width     = GenericTS(ts, lookback=lookback, eval_func=width, args=[self])
        self.upperband = GenericTS(ts, lookback=lookback, eval_func=upperband, args=[self])
        self.lowerband = GenericTS(ts, lookback=lookback, eval_func=lowerband, args=[self])

        self._sd        = sd
        self._ts        = ts
        self._cache     = []
        self._lookback  = lookback
        self.value     = None

    def evaluate(self):
        try:
            self.value = (self.upperband / self.lowerband - 1) * 100
        except:
            pass

    def onTick(self, price, timestamp, volume, action):
        raise NotImplementedError

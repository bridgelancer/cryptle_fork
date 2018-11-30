from cryptle.metric.base import Timeseries, GenericTS
from cryptle.metric.timeseries.wma import WMA

import numpy as np


def default(lookback):
    return [2 * (i + 1) / (lookback * (lookback + 1)) for i in range(lookback)]

class MACD(Timeseries):
    # MACD takes two timeseries. The two timeseries should update concurrently in order for a valid
    # value produed
    def __init__(self, fast, slow, lookback, name=None, weights=default):
        self._lookback = lookback
        self._ts       = [fast, slow]
        super().__init__(ts=self._ts)

        self._weights  = weights(lookback)
        self.value     = None


        def diff(fast, slow):
            try:
                return fast - slow
            except:
                return None

        def diff_ma(macd, weights, lookback):
            if len(macd.diff_ma._cache) == lookback:
                return np.average(macd.diff_ma._cache, axis=0, weights=weights)

        def signal(macd):
            if len(macd.diff_ma._cache) == lookback:
                return macd.diff - macd.diff_ma

        self.diff    = GenericTS([fast, slow], \
                            lookback=lookback, eval_func=diff, args=[fast, slow])
        self.diff_ma = GenericTS(self.diff, \
                            lookback=lookback, eval_func=diff_ma, args=[self, self._weights, lookback])
        self.signal   = GenericTS([self.diff, self.diff_ma], \
                            lookback=lookback, eval_func=signal, args=[self])


    def evaluate(self):
        pass

    def onTick(self, price, timestamp, volume, action):
        raise NotImplementedError

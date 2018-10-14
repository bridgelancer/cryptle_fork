from metric.base import Timeseries, GenericTS
from metric.timeseries.wma import WMA

import numpy as np


def default(lookback):
    return [2 * (i + 1) / (lookback * (lookback + 1)) for i in range(lookback)]

# how to solve the problem of two updates arising from two timeseries?
class MACD(Timeseries):
    # MACD takes two timeseries. The two timeseries should update concurrently in order for a valid
    # value produed
    def __init__(self, fast, slow, lookback, name=None, weights=default):
        self._lookback = lookback
        self._ts       = [fast, slow]
        super().__init__(ts=self._ts, name=name)
        self._weights  = weights(lookback)


        def diff(fast, slow):
            try:
                return float(fast) - float(slow)
            except:
                pass

        def diff_ma(macd, weights, lookback):
            if len(macd.diff_ma._cache) == lookback:
                return np.average(macd.diff_ma._cache, axis=0, weights=weights)

        self.diff      = GenericTS([fast, slow], lookback=lookback, eval_func=diff,
                args=[fast, slow])
        self.diff_ma   = GenericTS(self.diff, lookback=lookback, eval_func=diff_ma,
                args=[self, self._weights, lookback])
        #self.diff      = diff(self._fast, self._slow)
        #self.diff_ma   = diff_ma(self.diff, lookback, self._weights)
        self.value = None

    def evaluate(self):
        try:
            print(float(self.diff._ts[0]), float(self.diff._ts[1]))
            print(self.diff._cache)
            print("Diff", float(self.diff), '\n')
            print("Diff_ma", float(self.diff_ma), '\n')
            self.value = float(self.diff) - float(self.diff_ma)
        except:
            pass
        self.broadcast()

    def onTick(self, price, timestamp, volume, action):
        raise NotImplementedError

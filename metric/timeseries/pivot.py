from metric.base import Timeseries

class Pivot(Timeseries):
    def __init__(self, high, low, close, lookback, n=5, list=False):
        self._ts       = [high, low, close]
        super().__init__(ts=self._ts)
        self._lookback = lookback
        self._cache    = []
        self.value     = None
        self.pp        = PP(self._ts, looback)

        pp = self.pp
        pphl = [pp, high, low]
        self.r1        = R1([pp, low], lookback)
        self.s1        = S1([pp, high], lookback)
        # to consider how to encapsulate multiple RN/SN instances in pivot wrapper, now use lists to hold
        self.rn        = [RN(pphl, lookback, n) for range(1:n+1)]
        self.sn        = [SN(pphl, lookback, n) for range(1:n+1)]

        if list:
            self.onList()

    @Timeseries.cache
    def evaluate(self):
        self.broadcast()

    def onList(self):
        pass

# following pinescript documentation
class PP:
    def __init__(self, ts, lookback):
        super().__init__(ts=self_ts)
        self._ts       = ts
        self._high     = ts[0]
        self._low      = ts[1]
        self._close    = ts[2]
        self._lookback = lookback
        self.value     = None

    @Timeseries.cache
    def evaluate(self):
        self.value = (float(self._high) + float(self._low) + float(self._close))/ 3
        self.broadcast()

    def onList(self):
        pass

class R1:
    def __init__(self, ts, lookback):
        super().__init__(ts=self_ts)
        self._ts       = ts
        self._pp       = ts[0]
        self._low      = ts[1]
        self._lookback = lookback
        self.value     = None

    @Timeseries.cache
    def evaluate(self):
        self.value = (float(self._pp) + float(self._pp) + float(self._low))
        self.broadcast()

    def onList(self):
        pass

class S1:
    def __init__(self, ts, lookback):
        super().__init__(ts=self_ts)
        self._ts       = ts
        self._pp       = ts[0]
        self._high     = ts[1]
        self._lookback = lookback
        self.value     = None

    @Timeseries.cache
    def evaluate(self):
        self.value = (float(self._pp) - (float(self._high) - float(self._pp))
        self.broadcast()

    def onList(self):
        pass

class SN:
    def __init__(self, ts, lookback, n):
        if n < 2:
            raise ValueError
        super().__init__(ts=self_ts)
        self.n         = n
        self._ts       = ts
        self._pp       = ts[0]
        self._high     = ts[1]
        self._low      = ts[2]
        self._lookback = lookback
        self.value     = None

    @Timeseries.cache
    def evaluate(self):
        self.value = self._low - self.n * (self._high - self._pp)
        self.broadcast()

    def onList(self):
        pass


class RN:
    def __init__(self, ts, lookback, n):
        if n < 2:
            raise ValueError
        super().__init__(ts=self_ts)
        self.n         = n
        self._ts       = ts
        self._pp       = ts[0]
        self._high     = ts[1]
        self._low      = ts[2]
        self._lookback = lookback
        self.value     = None

    @Timeseries.cache
    def evaluate(self):
        self.value = self._high + self.n * (self._pp - self._low)
        self.broadcast()

    def onList(self):
        pass


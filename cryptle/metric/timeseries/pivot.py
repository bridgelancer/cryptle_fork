from cryptle.metric.base import Timeseries


class PivotPoints(Timeseries):
    def __init__(self, timestamp, interval, high, low, close, days=1, n=8, list=False):
        self._ts = [timestamp, close, high, low]
        super().__init__(ts=self._ts)
        self._days = days
        self._interval = interval
        self._lookback = int(
            (days * 24 * 60 * 60) / interval
        )  # the number of bars required to be cached
        self._cache = []
        self.period_high, self.period_low, self.period_close = None, None, None
        self.pp = None
        self.r = [None for i in range(n + 1)]
        self.s = [None for i in range(n + 1)]
        self.n = n
        self.value = self.pp
        self.timestamp = timestamp
        self.cabins = self.s[::-1] + self.r[1:]

        if list:
            self.onList()

    @Timeseries.cache
    def evaluate(self):
        if self.timestamp % (24 * 60 * 60) == 86400 - self._interval:
            # update the essential values of the previous period
            self.period_high = max([i[2] for i in self._cache])
            self.period_low = min([i[3] for i in self._cache])
            self.period_close = self._cache[-1][1]

            # calculate pivot point, support and resistance levels
            self.pp = (self.period_high + self.period_low + self.period_close) / 3

            self.r[0] = self.s[0] = self.pp
            self.r[1] = self.pp + (self.pp - self.period_low)
            self.s[1] = self.pp - (self.period_high - self.pp)
            for i in range(2, self.n + 1):
                self.r[i] = self.pp * (i - 1) + (
                    self.period_high - (i - 1) * self.period_low
                )
                self.s[i] = self.pp * (i - 1) - (
                    (i - 1) * self.period_high - self.period_low
                )

        self.cabins = self.s[::-1] + self.r[1:]
        self.value = self.pp

    def onList(self):
        pass

from cryptle.metric.base import Timeseries, MemoryTS

import logging

logger = logging.getLogger(__name__)


class PivotPoints(Timeseries):
    """ Hooked to the Timeseries system to receive updates for calculating PivotPoints

    Args
    ----
    timestamp : :class:`~cryptle.metric.timeseries.timestamp`
        Temporary solution to the lack of Time event in legacy versions.
    interval: float
        Equivalent to the bar length.
    high: :class:`~cryptle.metric.timeseries.candle.h`
        The high values processed by candles
    low: :class:`~cryptle.metric.timeseries.candle.h`
        The low values processed by candles
    close: :class:`~cryptle.metric.timeseries.candle.h`
        The close values processed by candles
    days: float, optional
        The number of days to refresh the PivotPoints, default to 1 day.
    n: int, optional
        Number of support and resistnace levels to store, default to 8.
    name : str, optional
        To be used by :meth:`__repr__` method for debugging

    Attributes
    ----------
    pp: float
        The R0 or S0 value.
    cabins: list
        A list of concatenated reversed(s) and r.
    r: list
        Holds the values of resistance levels, indexes from 0 to n.
    s: list
        Holds the values of support levels, indexes from 0 to n.

    """

    def __repr__(self):
        return self.name

    def __init__(
        self,
        timestamp,
        interval,
        high,
        low,
        close,
        days=1,
        n=8,
        list=False,
        name='pivot',
    ):
        self.name = f'{name}{interval}'
        self._ts = timestamp, close, high, low
        super().__init__(*self._ts)
        logger.debug(
            'Obj: {}. Initialized the parent Timeseries of PivotPoints.', type(self)
        )

        # parameters
        self._days = days
        self._interval = interval

        # the number of bars required to be cached
        self._lookback = int((days * 24 * 60 * 60) / interval)

        # local attributes to be used in computation
        self._period_high, self._period_low, self._period_close = None, None, None
        self._timestamp = timestamp
        self.n = n

        # Attributes
        self.pp = None
        self.r = [None for i in range(n + 1)]
        self.s = [None for i in range(n + 1)]
        self.cabins = self.s[::-1] + self.r[1:]
        self.value = self.pp

        self._cache = []

        if list:
            self.onList()

    @MemoryTS.cache('normal')
    def evaluate(self):
        logger.debug('Obj {} Calling evaluate in PivotPoints.', type(self))
        if self._timestamp % (24 * 60 * 60) == self._days * 86400 - self._interval:
            # update the essential values of the previous period
            self._period_high = max([i[2] for i in self._cache])
            self._period_low = min([i[3] for i in self._cache])
            self._period_close = self._cache[-1][1]

            # calculate pivot point, support and resistance levels
            self.pp = (self._period_high + self._period_low + self._period_close) / 3

            self.r[0] = self.s[0] = self.pp
            self.r[1] = self.pp + (self.pp - self._period_low)
            self.s[1] = self.pp - (self._period_high - self.pp)

            for i in range(2, self.n + 1):
                self.r[i] = self.pp * (i - 1) + (
                    self._period_high - (i - 1) * self._period_low
                )
                self.s[i] = self.pp * (i - 1) - (
                    (i - 1) * self._period_high - self._period_low
                )

        self.cabins = list(reversed(self.s)) + self.r[1:]
        self.value = self.pp

    def onList(self):
        pass

import logging

from cryptle.metric.base import Timeseries, MemoryTS

logger = logging.getLogger(__name__)


class BarReturn(Timeseries):
    """Timeseries for calculating the return based on Candle open and close values.

    Args
    ----
    bar: int, optional
        The number of bars to be calculated, should not be fewer than 1.
    all_open: bool, optional
        Use all open values to compute the return.
    all_close: bool, optional
        Use all close values to compute the return.

    Note: Default setting with bar=1 means that the latest close and latest open would
    be used.  Whereas for all_open/all_close=True, bar=1 means that latest open/close
    and previous open/close woule be used.

    """

    def __init__(self, o, c, bar=1, all_open=False, all_close=False):
        super().__init__(o, c)
        logger.debug('Obj:{}. Initialized the parent Timeseries of Return.', type(self))
        self._ts = o, c
        self.all_open = all_open
        self.all_close = all_close

        if not self.all_open and not self.all_close:
            self._lookback = bar
        else:
            self._lookback = bar + 1

        self._cache = []
        self.value = None

    @MemoryTS.cache('normal')
    def evaluate(self):
        logger.debug('Obj: {}. Calling evalute in Return.', type(self))
        if len(self._cache) == self._lookback:
            # format of items in self._cache: [[open, close], [open, close], ...]
            if not self.all_open and not self.all_close:
                self.value = (
                    self._cache[-1][1] - self._cache[-1 - (self._lookback - 1)][0]
                )
            elif self.all_open:
                self.value = (
                    self._cache[-1][0] - self._cache[-1 - (self._lookback - 1)][0]
                )
            elif self.all_close:
                self.value = (
                    self._cache[-1][1] - self._cache[-1 - (self._lookback - 1)][1]
                )
        self.broadcast()

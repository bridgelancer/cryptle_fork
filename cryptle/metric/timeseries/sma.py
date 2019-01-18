from cryptle.metric.base import Timeseries, MemoryTS
import numpy as np

import logging

logger = logging.getLogger(__name__)


class SMA(Timeseries):
    def __init__(self, ts, lookback, name="sma", list=False):
        """Timeseries for calculating the simple moving average of the upstream.

        Args
        ----
        lookback : The lookback period for calculating the SMA.

        """
        super().__init__(ts)
        logger.debug('Obj: {}. Initialized the parent Timeseries of SMA.', type(self))
        self._lookback = lookback
        self._ts = ts
        self._cache = []
        self.value = None
        if list:
            self.onList()

    # Any ts would call evaluate as new_candle emits. This updates its ts value for calculating the
    # correct value for output and further sourcing.
    @MemoryTS.cache('normal')
    def evaluate(self, candle=None):
        logger.debug('Obj {} Calling evaluate in SMA.', type(self))
        self.value = np.mean(self._cache)
        self.broadcast()

    def onList(self):
        pass
        # self.history = list(pd.DataFrame(self._ts).rolling(self._lookback).mean())

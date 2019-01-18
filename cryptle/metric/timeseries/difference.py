from cryptle.metric.base import Timeseries, MemoryTS
import numpy as np

import logging

logger = logging.getLogger(__name__)


class Difference(Timeseries):
    """Timeseries that computes the value of n-difference of any upstream.

    Args
    ---
    n : int, optional
        The integer for specifying the n-difference needed, default is 1.
    """

    def __init__(self, ts, n=1, name=None):
        super().__init__(ts)
        logger.debug(
            'Obj: {}. Initialized the parent Timeseries of Difference.', type(self)
        )
        self._ts = ts
        self._cache = []
        self._n = n
        self._lookback = self._n + 1
        self.value = None

    @MemoryTS.cache('normal')
    def evaluate(self):
        logger.debug('Obj {} Calling evaluate in Difference.', type(self))
        if len(self._cache) == self._lookback:
            output = np.diff(self._cache, self._n)
            self.value = output[-1]
            self.broadcast()

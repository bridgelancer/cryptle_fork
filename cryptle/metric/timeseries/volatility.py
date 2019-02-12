from cryptle.metric.base import Timeseries, MemoryTS
import numpy as np

import logging

logger = logging.getLogger(__name__)


class Volatility(Timeseries):
    """Timeseries that calculate the value of the 1/standard deviation of the sampled data

    Args
    ----
    lookback : int
        The lookback period for sampling and calculating the 1/sd.
    name : str, optional
        To be used by :meth:`__repr__` method for debugging

    """

    def __repr__(self):
        return self.name

    def __init__(self, ts, lookback, name='volatility'):
        self.name = f'{name}{lookback}'
        super().__init__(ts)
        logger.debug(
            'Obj: {}. Initialized the parent Timeseries of Volatility.', type(self)
        )
        self._lookback = lookback
        self._ts = ts
        self._cache = []

    @MemoryTS.cache('normal')
    def evaluate(self):
        logger.debug('Obj {} Calling evaluate in Volatility.', type(self))
        if np.std(self._cache) > 0:
            self.value = 1 / np.std(self._cache, ddof=1)
        else:
            self.value = 100

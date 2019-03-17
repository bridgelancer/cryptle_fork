from cryptle.metric.base import Timeseries, MemoryTS
import numpy as np

import cryptle.logging as logging

logger = logging.getLogger(__name__)


class SD(Timeseries):
    """Timeseries to calculate the value of standard deviation of upstream.

    Args
    ---
    lookback : int
        The lookback period for sampling and calculating the standard deviation.
    name : str, optional
        To be used by :meth:`__repr__` method for debugging

    """

    def __repr__(self):
        return self.name

    def __init__(self, ts, lookback, name='sd'):
        self.name = f'{name}{lookback}'
        super().__init__(ts)
        logger.debug('Obj: {}. Initialized the parent Timeseries of SD.', type(self))
        self._lookback = lookback
        self._ts = ts
        self.value = 0
        self._cache = []

    @MemoryTS.cache('normal')
    def evaluate(self):
        logger.debug('Obj {} Calling evaluate in SD.', type(self))
        calc = self._cache[:]
        if np.std(calc) > 0.001 * np.average(
            calc
        ):  # SHOULD SET TO A FRACTION OF THE MEAN VALUE OF THE SERIES
            self.value = 1 / np.std(calc, ddof=1)
        else:
            self.value = (float(self._ts) - np.average(calc)) / 0.001 * np.average(calc)

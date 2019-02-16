from cryptle.metric.base import Timeseries, MemoryTS
import scipy.stats as sp

import cryptle.logging as logging

logger = logging.getLogger(__name__)


class Skewness(Timeseries):
    """Timeseries for calculating the skewness of the upstream.

    Args
    ----
    lookback : int
        The lookback period for sampling upstream timeseries values.
    name : str, optional
        To be used by :meth:`__repr__` method for debugging

    """

    def __repr__(self):
        return self.name

    def __init__(self, ts, lookback, name='skewness', store_num=100):
        self.name = f'{name}{lookback}'
        super().__init__(ts, store_num=store_num)
        logger.debug(
            'Obj: {}. Initialized the parent Timeseries of Skewness.', type(self)
        )
        self._lookback = lookback
        self._ts = ts
        self._cache = []

    @MemoryTS.cache('normal')
    def evaluate(self):
        logger.debug('Obj {} Calling evaluate in WMA.', type(self))
        self.value = sp.skew(self._cache, bias=False)

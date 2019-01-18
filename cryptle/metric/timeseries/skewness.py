from cryptle.metric.base import Timeseries, MemoryTS
import scipy.stats as sp

import logging

logger = logging.getLogger(__name__)


class Skewness(Timeseries):
    """Timeseries for calculating the skewness of the upstream.

    Args
    ----
    lookback : int
        The lookback period for sampling upstream timeseries values.

    """

    def __init__(self, ts, lookback, name=None):
        super().__init__(ts)
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
        self.broadcast()

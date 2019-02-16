from cryptle.metric.base import Timeseries, MemoryTS
import scipy.stats as sp
import logging

logger = logging.getLogger(__name__)


class Kurtosis(Timeseries):
    """Timeseries that computes the value of kurtosis.

    Args
    ----
    lookback: int
        The looback period for calculating the sampled kurtosis.
    name : str, optional
        To be used by :meth:`__repr__` method for debugging

    Note: It is using the bias=False option of the scipy.stats.kurtosis function
    """

    def __repr__(self):
        return self.name

    def __init__(self, ts, lookback, name='kurtosis', store_num=100):
        self.name = f'{name}{lookback}'
        super().__init__(ts, store_num=store_num)
        logger.debug(
            'Obj: {}. Initialized the parent Timeseries of Kurtosis.', type(self)
        )
        self._lookback = lookback
        self._ts = ts
        self._cache = []
        self.value = None

    @MemoryTS.cache('normal')
    def evaluate(self):
        logger.debug('Obj {} Calling evaluate in Kurtosis.', type(self))
        self.value = sp.kurtosis(self._cache, bias=False)

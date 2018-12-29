from cryptle.metric.base import Timeseries
import scipy.stats as sp


class Kurtosis(Timeseries):
    """Timeseries that computes the value of kurtosis.

    Note: It is using the bias=False option of the scipy.stats.kurtosis function
    """

    def __init__(self, ts, lookback, name=None):
        super().__init__(ts)
        self._lookback = lookback
        self._ts = ts
        self._cache = []
        self.value = None

    @Timeseries.cache('normal')
    def evaluate(self):
        self.value = sp.kurtosis(self._cache, bias=False)
        self.broadcast()

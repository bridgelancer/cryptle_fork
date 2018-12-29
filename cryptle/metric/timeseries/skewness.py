from cryptle.metric.base import Timeseries
import scipy.stats as sp


class Skewness(Timeseries):
    """Timeseries for calculating the skewness of the upstream.

    Args
    ----
    lookback : int
        The lookback period for sampling upstream timeseries values.

    """

    def __init__(self, ts, lookback, name=None):
        super().__init__(ts)
        self._lookback = lookback
        self._ts = ts
        self._cache = []

    @Timeseries.cache('normal')
    def evaluate(self):
        self.value = sp.skew(self._cache, bias=False)
        self.broadcast()

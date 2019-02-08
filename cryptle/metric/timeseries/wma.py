from cryptle.metric.base import Timeseries, MemoryTS
import numpy as np

import logging

logger = logging.getLogger(__name__)


class WMA(Timeseries):
    """Timeseries for calculatig the weighted moving average of upstream.

    Args
    ----
    lookback : int
        The lookback period for sampling and calculating the WMA.
    weights: list, optional
        A list of weighting to weigh the past historical values, default to TradingView's
        implementaion

    """

    # Todo May be better to use a function just like EMA instead
    def __repr__(self):
        return self.name

    def __init__(self, ts, lookback, name="wma", weights=None):
        self.name = f'{name}{lookback}'
        super().__init__(ts)
        logger.debug('Obj: {}. Initialized the parent Timeseries of WMA.', type(self))
        self._lookback = lookback
        self._weights = weights or [
            2 * (i + 1) / (lookback * (lookback + 1)) for i in range(lookback)
        ]
        self._ts = ts
        self._cache = []
        self.value = None

    @MemoryTS.cache('normal')
    def evaluate(self):
        logger.debug('Obj {} Calling evaluate in WMA.', type(self))
        if len(self._cache) == self._lookback:
            self.value = np.average(self._cache, axis=0, weights=self._weights)

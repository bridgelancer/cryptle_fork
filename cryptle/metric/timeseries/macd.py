from cryptle.metric.base import Timeseries, GenericTS
from cryptle.metric.timeseries.wma import WMA

import numpy as np


def default(lookback):
    return [2 * (i + 1) / (lookback * (lookback + 1)) for i in range(lookback)]


class MACD(Timeseries):
    """The implementation of moving-average convergence divergence.

    This should take two moving-average Timeseries to initialize. The two upstreatm MAs should
    update concurrently. The updating behaviour of this class is ensured by the
    :class:`~cryptle.metric.base.Timeseries` implementaion.

    Args
    ---
    fast : :class:`~cryptle.metric.base.Timeseries`
        A moving-average Timeseries object with shorter lookback period.
    slow : :class:`~cryptle.metric.base.Timeseries`
        A moving-average Timeseries object with longer lookback period.
    lookback: int
        Lookback of the MACD object (or the signal period)

    """

    def __init__(self, fast, slow, lookback, name="macd", weights=default):
        self.name = name
        self._lookback = lookback
        super().__init__()

        self._weights = weights(lookback)
        self.value = None

        def diff(fast, slow):
            try:
                return fast - slow
            except:
                return None

        def diff_ma(macd, weights, lookback):
            if len(macd.diff_ma._cache) == lookback:
                return np.average(macd.diff_ma._cache, axis=0, weights=weights)

        def signal(macd):
            if len(macd.diff_ma._cache) == lookback:
                return macd.diff - macd.diff_ma

        self.diff = GenericTS(
            fast,
            slow,
            name="diff",
            lookback=lookback,
            eval_func=diff,
            args=[fast, slow],
            tocache=False,
        )
        self.diff_ma = GenericTS(
            self.diff,
            name="diff_ma",
            lookback=lookback,
            eval_func=diff_ma,
            args=[self, self._weights, lookback],
        )

        self.signal = GenericTS(
            self.diff,
            self.diff_ma,
            name="signal",
            lookback=lookback,
            eval_func=signal,
            args=[self],
        )

    def evaluate(self):
        pass

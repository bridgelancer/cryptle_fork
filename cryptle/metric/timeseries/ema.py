from cryptle.metric.base import Timeseries
import logging

logger = logging.getLogger(__name__)


def default(lookback):
    return 2 / (lookback + 1)


class EMA(Timeseries):
    """Timeseries that computes the exponential moving average of some Timeseries.

    Args
    ----
    lookback: int
        The lookback period for sampling and calculating the EMA.
    weight: function
        A function that returns a fraction (smaller than 1 in value)
    name : str, optional
        To be used by :meth:`__repr__` method for debugging

    """

    def __repr__(self):
        return self.name

    def __init__(self, ts, lookback, name="ema", weight=default):
        self.name = f'{name}{lookback}'
        super().__init__(ts)
        logger.debug('Obj: {}. Initialized the parent Timeseries of EMA.', type(self))
        self._lookback = lookback
        self._weight = weight(
            lookback
        )  # weight is a math function that takes lookback as argument and returns a float in range (0, 1)
        self._ts = ts
        self.value = None

    def evaluate(self):
        logger.debug('Obj {} Calling evaluate in EMA.', type(self))
        if self.value is None:
            self.value = float(self._ts)
        else:
            self.value = (
                float(self._ts) * self._weight + (1 - self._weight) * self.value
            )

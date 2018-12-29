from cryptle.metric.base import Timeseries


def default(lookback):
    return 2 / (lookback + 1)


class EMA(Timeseries):
    """Timeseries that computes the exponential moving average of some Timeseries."""

    def __init__(self, ts, lookback, name="ema", weight=default, bar=False):
        self.name = name
        super().__init__(ts)
        self._lookback = lookback
        self._weight = weight(
            lookback
        )  # weight is a math function that takes lookback as argument and returns a float in range (0, 1)
        self._ts = ts
        self.value = None
        self._bar = bar

    def evaluate(self, candle=None):
        if self.value is None:
            self.value = float(self._ts)
        else:
            self.value = (
                float(self._ts) * self._weight + (1 - self._weight) * self.value
            )
        self.broadcast()

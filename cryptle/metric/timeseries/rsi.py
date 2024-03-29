from cryptle.metric.base import Timeseries

import cryptle.logging as logging

logger = logging.getLogger(__name__)


def default(lookback):
    return 1 / lookback


class RSI(Timeseries):
    """ Timeseries that calculate the relative strenth index of the upstreatm.

    Args
    ----
    lookback : int
        The lookback period for calculating RSI.
    default : function, optional
        The weighing function for the EMA calculation, default to be 1/lookback.
    name : str, optional
        To be used by :meth:`__repr__` method for debugging

    Note: Complies with the TradingView value

    """

    def __repr__(self):
        return self.name

    def __init__(self, ts, lookback, name="rsi", weight=default):
        self.name = f'{name}{lookback}'
        super().__init__(ts)
        logger.debug('Obj: {}. Initialized the parent Timeseries of RSI.', type(self))
        self._lookback = lookback
        self._ts = ts
        self._cache = []
        self._weight = weight(lookback)
        self._up = []
        self._down = []
        self._ema_up = None
        self._ema_down = None

    def evaluate(self):
        logger.debug('Obj {} Calling evaluate in RSI.', type(self))
        self._cache.append(float(self._ts))
        if len(self._cache) < 2:
            return

        # Calculate gain/lose
        if self._cache[-1] > self._cache[-2]:
            self._up.append(abs(self._cache[-1] - self._cache[-2]))
            self._down.append(0)
        else:
            self._down.append(abs(self._cache[-1] - self._cache[-2]))
            self._up.append(0)

        # Return if insufficient
        if len(self._up) < self._lookback or len(self._down) < self._lookback:
            return

        # keep the length of list of gain and loss to be the same as lookback
        if len(self._up) > self._lookback:
            self._up = self._up[-self._lookback :]
        if len(self._down) > self._lookback:
            self._down = self._down[-self._lookback :]

        if len(self._cache) > 2:
            self._cache = self._cache[-2:]

        price_up = self._up[-1]
        price_down = self._down[-1]

        # calculation of 'average gain' and 'average loss'
        if self._ema_up is None and self._ema_down is None:
            self._ema_up = sum([x for x in self._up]) / len(self._up)
            self._ema_down = sum([x for x in self._down]) / len(self._down)
            try:
                self.value = 100 - 100 / (1 + self._ema_up / self._ema_down)
            except ZeroDivisionError:
                if self._ema_down == 0 and self._ema_up != 0:
                    self.value = 100
                elif self._ema_up == 0 and self._ema_down != 0:
                    self.value = 0
                elif self._ema_up == 0 and self._ema_down == 0:
                    self.value = 50
            return

        self._ema_up = self._weight * price_up + (1 - self._weight) * self._ema_up
        self._ema_down = self._weight * price_down + (1 - self._weight) * self._ema_down

        # calculation of RSI
        try:
            self.value = 100 - 100 / (1 + self._ema_up / self._ema_down)
        except ZeroDivisionError:
            if self._ema_down == 0 and self._ema_up != 0:
                self.value = 100
            elif self._ema_up == 0 and self._ema_down != 0:
                self.value = 0
            elif self._ema_up == 0 and self._ema_down == 0:
                self.value = 50

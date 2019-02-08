from cryptle.metric.base import MultivariateTS, GenericTS
import numpy as np

import logging

logger = logging.getLogger(__name__)


# Todo(MC) Could consider rewrite to take individual candle.c, candle.h, candle.l instaed
class ATR(MultivariateTS):
    """Compute the ATR value based on Candle input.

    Args
    ----
    candle: :class:`~cryptle.metric.timeseries.candle.CandleStick`
        CandleStick object for updating

    name : str, optional
        To be used by :meth:`__repr__` method for debugging
    """

    def __repr__(self):
        return self.name

    def __init__(self, candle, lookback, name='atr'):
        self.name = f'{name}{lookback}'
        self._lookback = lookback
        self.prev_value = None

        def true_range(atr):
            if len(atr._cache) >= 3:
                last_close = atr._cache[-3][0]
                high = atr._cache[-2][1]
                low = atr._cache[-2][2]

            if atr.value is None and len(atr._cache) == atr._lookback:
                return np.mean([x[1] for x in atr._cache]) - np.mean(
                    [x[2] for x in atr._cache]
                )
            elif atr.value is not None:
                t1 = float(high) - float(low)
                t2 = abs(float(high) - float(last_close))
                t3 = abs(float(low) - float(last_close))
                return max(t1, t2, t3)

        def value(atr):
            try:
                if atr.prev_value is None:
                    return float(self._tr)
                else:
                    return (
                        atr.prev_value * (self._lookback - 1) + float(self._tr)
                    ) / self._lookback
            except:
                pass

        self._tr = GenericTS(
            candle.c,
            candle.h,
            candle.l,
            lookback=lookback,
            eval_func=true_range,
            args=[self],
        )  # tr is the true_range object to be passed into the "ATR" wrapper
        self.value = GenericTS(
            self._tr, lookback=lookback, eval_func=value, args=[self]
        )
        logger.debug(
            'Obj:{}. Finished declaration of all Timeseries objects', type(self)
        )
        super().__init__(candle.c, candle.h, candle.l)
        logger.debug(
            'Obj: {}. Initialized the parent MultivariateTS of BollingerBand',
            type(self),
        )
        logger.debug('Obj: {}. Initialized BollingerBand', type(self))

    def evaluate(self):
        logger.debug('Obj: {} Calling evaluate in bollinger', type(self))

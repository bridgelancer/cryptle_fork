from cryptle.metric.base import GenericTS, MultivariateTS
from cryptle.metric.timeseries.ema import EMA

import cryptle.logging as logging
import numpy as np

logger = logging.getLogger(__name__)


class MACDEMA(MultivariateTS):
    """The wrapper implementation of moving-average convergence divergence.

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
    name : str, optional
        To be used by :meth:`__repr__` method for debugging

    Attributes
    ---
    diff : :class:`cryptle.metric.base.GenericTS`
        The Timeseries object for calculating the difference between fast and slow MAs.
    diff_ma : :class:`cryptle.metric.base.GenericTS`
        The Timeseries object for calculating the moving-average of the diff attribute.
    signal : :class:`cryptle.metric.base.GenericTS`
        The Timeseries object for calculating the difference between diff and diff_ma
        attribute.

    """

    def __repr__(self):
        return self.name

    def __init__(
        self, fast, slow, lookback, name="macd", store_num=100
    ):
        self.name = f'{name}{fast._lookback}_{slow._lookback}_{lookback}'
        self._lookback = lookback

        def diff(fast, slow):
            try:
                return fast - slow
            except:
                return None


        def signal(macd):
            return macd.diff - macd.diff_ma

        self.diff = GenericTS(
            fast,
            slow,
            name="diff",
            lookback=int(lookback),
            eval_func=diff,
            args=[fast, slow],
            tocache=False,
            store_num=store_num,
        )

        self.diff_ma = EMA(self.diff, lookback)

        self.signal = GenericTS(
            self.diff,
            self.diff_ma,
            name="signal",
            lookback=int(lookback),
            eval_func=signal,
            args=[self],
            store_num=store_num,
        )

        logger.debug(
            'Obj: {}. Finished declaration of all Timeseries objects', type(self)
        )
        super().__init__(fast, slow)
        logger.debug(
            'Obj: {}. Initialized the parent MultivariateTS of MACD', type(self)
        )
        logger.debug('Obj: {}. Initialized MACD', type(self))

    def evaluate(self):
        logger.debug('Obj: {} Calling evaluate in MACD', type(self))

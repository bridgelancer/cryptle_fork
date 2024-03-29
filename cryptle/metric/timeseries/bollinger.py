from cryptle.metric.base import Timeseries, GenericTS, MultivariateTS
import numpy as np
import cryptle.logging as logging

logger = logging.getLogger(__name__)


class BollingerBand(MultivariateTS):
    """Wrapper class that holds the subseries for upperband, lowerband and bandwidth and value
    of a common Bollingerband.

    Args
    ----
    lookback: int
        The lookback period for sampling and calculating the BollingerBand suite
    sd: float, optional
        The desired standard deviation for the object to calculate, default to 2
    upper_sd: float, optional
        Default to value of ``sd``. Specify the upperband of the BollingerBand suite
    lower_sd: float, optional
        Default to value of ``sd``. Specify the lowerband of the BollingerBand suite
    name : str, optional
        To be used by :meth:`__repr__` method for debugging

    Attributes
    ----------
    width: :class:`~cryptle.metric.base.GenericTS`
        Timeseries object that calculates and updates the bollinger band width.
    upperband: :class:`~cryptle.metric.base.GenericTS`
        Timeseries object that calculates and updates the upperband value of BollingerBand
    lowerband: :class:`~cryptle.metric.base.GenericTS`
        Timeseries object that calculates and updates the lowerband value of BollingerBand
    value: :class:`~cryptle.metric.base.GenericTS`
        Timeseries object that calculates and updates the bollinger band percentage.

    Note: Terminology adopted from TradingView

    """

    def __repr__(self):
        return self.name

    def __init__(
        self, ts, lookback, sd=2, upper_sd=None, lower_sd=None, name='bollinger'
    ):
        self.name = f'{name}{lookback}'
        if upper_sd is None:
            uppersd = sd
        else:
            self._uppersd = upper_sd

        if lower_sd is None:
            lowersd = sd
        else:
            lowersd = lower_sd

        def width(bb):
            return np.std(bb.width._cache, ddof=0)

        def upperband(bb):
            return sum(bb.upperband._cache) / lookback + uppersd * float(bb.width)

        def lowerband(bb):
            return sum(bb.lowerband._cache) / lookback - lowersd * float(bb.width)

        def value(bb):
            return (bb.upperband / bb.lowerband - 1) * 100

        self.width = GenericTS(ts, lookback=lookback, eval_func=width, args=[self])
        self.upperband = GenericTS(
            ts, lookback=lookback, eval_func=upperband, args=[self]
        )
        self.lowerband = GenericTS(
            ts, lookback=lookback, eval_func=lowerband, args=[self]
        )
        self.value = GenericTS(ts, lookback=lookback, eval_func=value, args=[self])

        # The MultivariateTS initialization must come ***AFTER** all the Timeseries-(derived)
        # objects in order to ensure proper updating
        logger.debug(
            'Obj: {}. Finished declaration of all Timeseries objects', type(self)
        )
        super().__init__(ts)
        logger.debug(
            'Obj: {}. Initialized the parent MultivariateTS of BollingerBand',
            type(self),
        )
        logger.debug('Obj: {}. Initialized BollingerBand', type(self))

    def evaluate(self):
        logger.debug('Obj: {} Calling evaluate in bollinger', type(self))

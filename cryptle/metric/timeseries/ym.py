import logging
import math

from cryptle.metric.base import Timeseries, MemoryTS

logger = logging.getLogger(__name__)


class YM(Timeseries):
    """Timeseries for calculating the Yeung's momentum(YM) based on Return values.

    Args
    ----
    r: :class:`~cryptle.metric.base.timeseries.barreturn.BarReturn`
        One-bar return Timeseries object, calculating with bar close - bar open.
        Default to lookback 6 bars.
    lookback: int, optional
        Number of bars to lookback for computing the value for YM.

    """

    def __init__(self, r, lookback=6):
        super().__init__(r)
        logger.debug('Obj:{}. Initialized the parent Timeseries of YM.', type(self))
        self._ts = r

        self._lookback = lookback
        self._cache = []
        self.value = None

    @MemoryTS.cache('normal')
    def evaluate(self):

        if len(self._cache) != self._lookback:
            return

        prev_mo = 0
        abs_prev_mo = 0
        val = 0

        for ret in self._cache:
            # sign is the sign of ret
            if ret != 0:
                sign = math.copysign(1, ret)
            else:
                sign = 0

            # initialize: add the val to sign
            if prev_mo == 0:
                prev_mo = sign
                val += sign
            # if sign of previous momentum equal to current sign return
            elif math.copysign(1, prev_mo) == sign:
                abs_prev_mo = math.fabs(prev_mo) + 0.5
                prev_mo = math.copysign(abs_prev_mo, prev_mo)
                val += prev_mo
            # if sign of previous momentum does not equal to current sign of return
            elif math.copysign(1, prev_mo) != sign:
                prev_mo = sign
                val += sign

        self.value = val
        self.broadcast()

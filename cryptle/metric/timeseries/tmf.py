from cryptle.metric.base import MultivariateTS, GenericTS, MemoryTS
from cryptle.metric.timeseries.ema import EMA
import numpy as np

import logging

logger = logging.getLogger(__name__)

class TMF(MultivariateTS):
    """Compute the Twiggs Money Flow.

    The actual reference for the implementaion is
    [this](https://www.incrediblecharts.com/indicators/twiggs_money_flow.php#twiggs_money_flow_welles_wilders_indicators).

    Args
    ----
    ytd_close: :class:`~cryptle.metric.base.GenericTS`
        A GenericTS object that gives the most updated yesterday close

    current_high::class:`~cryptle.metric.base.GenericTS`
        A GenericTS object that gives the current day high

    current_low: :class:`~cryptle.metric.base.GenericTS`
        A GenericTS object that gives the current day low

    candle: :class:`~cryptle.metric.timeseries.candle.CandleStick`
        CandleStick object for updating

    name: str, optional
        To be used by :meth:`__repr__` method for debugging
    """

    def __repr__(self):
        return self.name


    def __init__(self, ytd_close, current_high, current_low, current_vol, candle, lookback=21, name='tmf', store_num=100):
        self.name = f'{name}{lookback}'
        super().__init__(ytd_close, current_high, current_low, current_vol, candle.v)
        self._lookback = lookback
        self._ts = ytd_close, current_high, current_low, candle.c, candle.v
        self._cache = []

        def TRH(ytd_close, curent_high):
            return max(ytd_close, current_high)

        def TRL(ytd_close, current_low):
            return min(ytd_close, current_low)

        def AD(trh, trl, close, volume):
            print(trl, trh, close, volume)
            return ((close - trl) - (trh - close)) / (trh - trl) * volume

        # GenericTS definition

        trh_name = f'trh_{lookback}'
        trl_name = f'trl_{lookback}'
        ad_name = f'ad_{lookback}'

        self.trh = GenericTS(
                ytd_close,
                current_high,
                name=trh_name,
                lookback=lookback,
                eval_func=TRH,
                args=[ytd_close, current_high],
                store_num=store_num,
            )

        self.trl = GenericTS(
                ytd_close,
                current_low,
                name=trl_name,
                lookback=lookback,
                eval_func=TRL,
                args=[ytd_close, current_low],
                store_num=store_num,
            )

        self.ad_raw = GenericTS(
                self.trh,
                self.trl,
                current_vol,
                name=ad_name,
                lookback=lookback,
                eval_func=AD,
                args=[self.trh, self.trl, candle.c, current_vol],
                store_num=store_num,
            )

        self.ad = EMA(self.ad_raw, lookback)
        self.ema_volume = EMA(candle.v, lookback)

    def evaluate(self):
        pass

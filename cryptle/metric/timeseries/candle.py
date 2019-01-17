from cryptle.metric.base import Timeseries, GenericTS
from cryptle.event import on, Bus

"""Candle-related Timeseries object.

These objects are unique as client must pass a candle-like object that is in a format analgous to [o,
c, h, l, (v)] in order to initialize this Timeseries.

This exists as a result of the segregation of responsibility. The aggregating responsibility of
ticksticks are extracted out to :class:`~cryptle.aggregator`. This class serves as an portal for
other Timeseries to retrieve ready-to-use Candle data from initializing their own cache and
calculating their own values.

"""

import logging

logger = logging.getLogger(__name__)

# TODO - Segregate Observer/Observable pattern from Timeseries baseclass to allow CandleStick to
# change to non TS-type object
def Open(lst):
    return lst[-1][0]


def Close(lst):
    return lst[-1][1]


def High(lst):
    return lst[-1][2]


def Low(lst):
    return lst[-1][3]


def Volume(lst):
    return lst[-1][5]


def cache(ts):
    return ts.value


class CandleStick:
    """ Extracted wrapper function of the original CandleBar class """

    def __repr__(self):
        return self.name

    def __init__(
        self,
        lookback,
        bar=False,
        Open=Open,
        Close=Close,
        High=High,
        Low=Low,
        Volume=Volume,
        name='candle',
    ):
        self._lookback = lookback
        self._ts = []
        self.name = name

        # eval_func for GenericTS objects
        self._o_cache = GenericTS(
            name="open_cache",
            lookback=lookback,
            eval_func=Open,
            args=[self._ts],
            tocache=False,
        )
        self._c_cache = GenericTS(
            name="close_cache",
            lookback=lookback,
            eval_func=Close,
            args=[self._ts],
            tocache=False,
        )
        self._h_cache = GenericTS(
            name="high_cache",
            lookback=lookback,
            eval_func=High,
            args=[self._ts],
            tocache=False,
        )
        self._l_cache = GenericTS(
            name="low_cache", lookback=lookback, eval_func=Low, args=[self._ts], tocache=False

        )
        self._v_cache = GenericTS(
            name="volume_cache",
            lookback=lookback,
            eval_func=Volume,
            args=[self._ts],
            tocache=False,
        )

        self.o = GenericTS(
            self._o_cache,
            name='open',
            lookback=lookback
            eval_func=cache,
            args=[self._o_cache],
            tocache=True,
        )

        self.c = GenericTS(
            self._c_cache,
            name='close',
            lookback=lookback
            eval_func=cache,
            args=[self._c_cache],
            tocache=True,
        )

        self.h = GenericTS(
            self._h_cache,
            name='high',
            lookback=lookback
            eval_func=cache,
            args=[self._h_cache],
            tocache=True,
        )

        self.l = GenericTS(
            self._l_cache,
            name='low',
            lookback=lookback
            eval_func=cache,
            args=[self._l_cache],
            tocache=True,
        )

        self.v = GenericTS(
            self._v_cache,
            name='volume',
            lookback=lookback
            eval_func=cache,
            args=[self._v_cache],
            tocache=True,
        )
        self.bar = bar

    # CandleStick has a unique :meth:`source` that makes itself a timeseries generating source
    # todo(MC): segregate abstraction layer appropriately
    @on('new_candle')
    @on('aggregator:new_candle')
    def source(self, data):
        self._ts.append(data)
        self.update()

    def update(self):
        # eval_func passed to GenericTS objects held within CandleStick
        self._o_cache.evaluate()
        self._c_cache.evaluate()
        self._h_cache.evaluate()
        self._l_cache.evaluate()
        self._v_cache.evaluate()

    def shred(self):
        if len(self._ts) >= 30:
            self._ts = self._ts[-30:]
        else:
            pass

    def accessBar():
        return [float(x) for x in [self.o, self, c, self.h, self.l, self.v]]

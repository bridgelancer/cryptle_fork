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
    return lst[-1][4]


class CandleStick:
    """ Extracted wrapper function of the original CandleBar class """

    def __init__(
        self,
        lookback,
        bar=False,
        Open=Open,
        Close=Close,
        High=High,
        Low=Low,
        Volume=Volume,
    ):
        self._lookback = lookback
        self._ts = []
        # eval_func for GenericTS objects
        self.o = GenericTS(
            name="open",
            lookback=lookback,
            eval_func=Open,
            args=[self._ts],
            tocache=False,
        )
        self.c = GenericTS(
            name="close",
            lookback=lookback,
            eval_func=Close,
            args=[self._ts],
            tocache=False,
        )
        self.h = GenericTS(
            name="high",
            lookback=lookback,
            eval_func=High,
            args=[self._ts],
            tocache=False,
        )
        self.l = GenericTS(
            name="low", lookback=lookback, eval_func=Low, args=[self._ts], tocache=False
        )
        self.v = GenericTS(
            name="volume",
            lookback=lookback,
            eval_func=Volume,
            args=[self._ts],
            tocache=False,
        )
        self.bar = bar

    # CandleStick has a unique function source that makes itself a ts generating source
    # todo(MC): segregate abstraction layer appropriately
    @on('new_candle')
    @on('aggregator:new_candle')
    def source(self, data):
        self._ts.append(data)
        self.update()

    def update(self):
        # eval_func passed to GenericTS objects held within CandleStick
        self.o.evaluate()
        self.c.evaluate()
        self.h.evaluate()
        self.l.evaluate()
        self.v.evaluate()

    # Todo temporariliy disabled pruning - some buggy behaviour causing downstream TS objects fail to update
    # after 365 bars while self._ts is pruned appropriately
    def shred(self):
        if len(self._ts) >= 30:
            self._ts = self._ts[-30:]
        else:
            pass

    def accessBar():
        return [float(x) for x in [self.o, self, c, self.h, self.l, self.v]]

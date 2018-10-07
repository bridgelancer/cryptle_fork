from metric.base import Timeseries
from cryptle.event import source, on, Bus

'''Candle-related Timeseries object.

These objecbar are unique as client must pass a candle-like object that is in a format similar to [o,
c, h, l, (v)] in order to initialize these Timeseries. This makes intuitive sense as these objecbar
are not aggregating facility of ticks but rather a reducing facility that output the latest value of
the aggreagated bar. There is currently no generic bar aggregating objecbar
implemented for the new Timeseries paradigm.

'''

class CandleStick(Timeseries):
    ''' Extracted wrapper function of the original CandleBar class'''
    def __init__(self, lookback, bar=False, bus=None):
        super().__init__()
        self._lookback = lookback
        # self._ts needs pruning in this case - @TODO
        self._ts       = []
        self.o         = Open(self._ts, lookback)
        self.c         = Close(self._ts, lookback)
        self.h         = High(self._ts, lookback)
        self.l         = Low(self._ts, lookback)
        self.value     = None
        self.bar       = bar
        if isinstance(bus, Bus):
            bus.bind(self)

    # CandleStick has a unique functino appendTS that makes itself a ts generating source

    @on('aggregator:new_candle')
    def appendTS(self, data):
        self._ts.append(data)
        self.evaluate()
        self.prune()
        self.broadcast()

    def prune(self):
        if len(self._ts) > 365:
            self._ts = self._ts[-365:]

    def evaluate(self):
        self.o.evaluate()
        self.c.evaluate()
        self.h.evaluate()
        self.l.evaluate()

        # the evaluate function should automatically push a bar to self._cache
        try:
            self.value = float(self.o) # use self.o is the default value
        except:
            self.value = None

    def accessBar():
        return [float(x) for x in [self.o, self, c, self.h, self.l, self.v]]

class Open(Timeseries):

    def __init__(self, ts, lookback, name=None):
        super().__init__(ts=ts, name=name)
        self._lookback  = lookback
        self._ts        = ts
        self.value      = None

    @Timeseries.cache
    def evaluate(self):
        try:
            self.value = self._ts[-1][0]
            self.broadcast()
        except:
            self.value = None

class Close(Timeseries):

    def __init__(self, ts, lookback, name=None):
        super().__init__(ts=ts, name=name)
        self._lookback = lookback
        self._ts       = ts
        self.value     = None

    def evaluate(self):
        self.value = self._ts[-1][1]
        self.broadcast()

class High(Timeseries):

    def __init__(self, ts, lookback, name=None):
        super().__init__(ts=ts, name=name)
        self._lookback = lookback
        self._ts      = ts
        self.value     = None

    def evaluate(self):
        self.value = self._ts[-1][2]
        self.broadcast()

class Low(Timeseries):

    def __init__(self, ts, lookback, name=None):
        super().__init__(ts=ts, name=name)
        self._lookback = lookback
        self._ts      = ts
        self.value     = None

    def evaluate(self):
        self.value = self._ts[-1][3]
        self.broadcast()

class Volume(Timeseries):

    def __init__(self, ts, lookback, name=None):
        super().__init__(ts=ts, name=name)
        self._lookback = lookback
        self._ts      = ts
        self.vallue    = None

    def evaluate(self):
        self.value = self._ts[-1][4]
        self.broadcast()

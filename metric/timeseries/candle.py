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
    def __init__(self, lookback, bus=None):
        self._lookback = lookback
        self._ts       = []
        self._cache    = []
        self.output    = []
        self.o         = Open(self._ts, lookback)
        self.c         = Close(self._ts, lookback)
        self.h         = High(self._ts, lookback)
        self.l         = Low(self._ts, lookback)
        self.value     = None
        if isinstance(bus, Bus):
            bus.bind(self)

    # CandleStick has a unique functino appendTS that makes itself a ts generating source
    @on('aggregator:new_candle')
    def appendTS(self, data):
        self._ts.append(data)
        self.onCandle()

    @Timeseries.cache
    def onCandle(self):
        self.o.onCandle()
        self.c.onCandle()
        self.h.onCandle()
        self.l.onCandle()

        # the onCandle function should automatically push a bar to self._cache
        try:
            self.value = float(self.o) # use self.o is the default value
            self.output.append(self.value)
        except:
            self.value = None

class Open(Timeseries):

    def __init__(self, bar, lookback):
        self._lookback  = lookback
        self._ts        = bar
        self.value      = None

    @Timeseries.cache
    def onCandle(self):
        try:
            self.value = self._ts[-1][0]
        except:
            self.value = None

class Close(Timeseries):

    def __init__(self, bar, lookback):
        self._lookback = lookback
        self._ts       = bar
        self.value     = None

    def onCandle(self):
        self.value = self._ts[-1][1]

class High(Timeseries):

    def __init__(self, bar, lookback):
        self._lookback = lookback
        self._ts      = bar
        self.value     = None

    def onCandle(self):
        self.value = self._ts[-1][2]

class Low(Timeseries):

    def __init__(self, bar, lookback):
        self._lookback = lookback
        self._ts      = bar
        self.value     = None

    def onCandle(self):
        self.value = self._ts[-1][3]

class Volume(Timeseries):

    def __init__(self, bar, lookback):
        self._lookback = lookback
        self._ts      = bar
        self.vallue    = None

    def onCandle(self):
        self.value = self._ts[-1][4]

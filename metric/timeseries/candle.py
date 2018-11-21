from metric.base import Timeseries, GenericTS
from cryptle.event import on, Bus

'''Candle-related Timeseries object.

These objects are unique as client must pass a candle-like object that is in a format similar to [o,
c, h, l, (v)] in order to initialize these Timeseries. This makes intuitive sense as these objecbar
are not aggregating facility of ticks but rather a reducing facility that output the latest value of
the aggreagated bar. There is currently no generic bar aggregating objecbar
implemented for the new Timeseries paradigm.

'''

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

class CandleStick(Timeseries):
    """ Extracted wrapper function of the original CandleBar class """
    def __init__(self, lookback, bar=False, bus=None, Open=Open, Close=Close, High=High, Low=Low,
            Volume=Volume):
        super().__init__()
        self._lookback = lookback
        # self._ts needs pruning in this case - @TODO
        self._ts       = []
        # eval_func for GenericTS objects
        self.o         = GenericTS(self._ts, lookback=lookback, eval_func=Open,  args=[self._ts])
        self.c         = GenericTS(self._ts, lookback=lookback, eval_func=Close, args=[self._ts])
        self.h         = GenericTS(self._ts, lookback=lookback, eval_func=High,  args=[self._ts])
        self.l         = GenericTS(self._ts, lookback=lookback, eval_func=Low,   args=[self._ts])
        self.v         = GenericTS(self._ts, lookback=lookback, eval_func=Volume,args=[self._ts])
        self.value     = None
        self.bar       = bar
        if isinstance(bus, Bus):
            bus.bind(self)

    # CandleStick has a unique functino appendTS that makes itself a ts generating source
    @on('aggregator:new_candle')
    def appendTS(self, data):
        self._ts.append(data)
        self.evaluate()
        self.broadcast()
        self.prune()

    def evaluate(self):
        # eval_func passed to GenericTS objects held within CandleStick
        self.o.evaluate()
        self.c.evaluate()
        self.h.evaluate()
        self.l.evaluate()
        self.v.evaluate()

        # the evaluate function should automatically push a bar to self._cache
        try:
            self.value = float(self.o) # use self.o is the default value
        except:
            self.value = None

    # @TODO temporariliy disabled pruning - buggy behaviour causing downstream TS objects fail to update
    # after 365 bars while self._ts remains pruned
    def prune(self):
        #if len(self._ts) >= 365:
        #   self._ts = self._ts[-365:]
        pass

    def accessBar():
        return [float(x) for x in [self.o, self, c, self.h, self.l, self.v]]

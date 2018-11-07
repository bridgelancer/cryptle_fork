"""
Base classes for time series data structures.

Warning
-------
The class names TimeseriesWrapper, Timeseries, and HistoricalTS are temporary
and are subject to change.
"""

from functools import wraps

import logging
import csv

class Metric:
    """Base class with common functions of single valued metrics"""

    def __int__(self):
        return int(self.value)

    def __float__(self):
        return float(self.value)

    def __neg__(self):
        return -self.value

    def __abs__(self):
        return abs(self.value)

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return str(self.value)

    def __bool__(self):
        return bool(self.value)

    def __eq__(self, other):
        return self.value == other

    def __ne__(self, other):
        return self.value != other

    def __lt__(self, other):
        return self.value < other

    def __gt__(self, other):
        return self.value > other

    def __le__(self, other):
        return self.value <= other

    def __ge__(self, other):
        return self.value >= other

    def __add__(self, other):
        return self.value + other

    def __sub__(self, other):
        return self.value - other

    def __mul__(self, other):
        return self.value * other

    def __truediv__(self, other):
        return self.value / other

    def __floordiv__(self, other):
        return self.value // other

    def __divmod__(self, other):
        return divmod(self.value, other)

    def __mod__(self, other):
        return self.value % other

    def __pow__(self, other):
        return self.value ** other

    def __radd__(self, other):
        return other + self.value

    def __rsub__(self, other):
        return other - self.value

    def __rmul__(self, other):
        return other * self.value

    def __rtruediv__(self, other):
        return other / self.value

    def __rfloordiv__(self, other):
        return other // self.value

    def __rdivmod__(self, other):
        return divmod(other, self.value)

    def __rmod__(self, other):
        return other % self.value

    def __rpow__(self, other):
        return other ** self.value


class Candle:
    """Mutable candle stick with namedtuple-like API."""

    def __init__(self, o, c, h, l, t, v, nv):
        self._bar = [o, c, h, l, t, v, nv]

    def __int__(self):
        return int(self._bar[0])

    def __float__(self):
        return float(self._bar[0])

    def __getitem__(self, item):
        return self._bar[item]

    def __repr__(self):
        return "Candle({})".format(self._bar.__repr__())

    @property
    def open(self):
        return self._bar[0]

    @property
    def close(self):
        return self._bar[1]

    @property
    def high(self):
        return self._bar[2]

    @property
    def low(self):
        return self._bar[3]

    @property
    def timestamp(self):
        return self._bar[4]

    @property
    def volume(self):
        return self._bar[5]

    @property
    def netvol(self):
        return self._bar[6]

    @open.setter
    def open(self, value):
        self._bar[0] = value

    @close.setter
    def close(self, value):
        self._bar[1] = value

    @high.setter
    def high(self, value):
        self._bar[2] = value

    @low.setter
    def low(self, value):
        self._bar[3] = value

    @timestamp.setter
    def timestamp(self, value):
        self._bar[4] = value

    @volume.setter
    def volume(self, value):
        self._bar[5] = value

    @netvol.setter
    def netvol(self, value):
        self._bar[6] = value

class Model:
    """Base class for holding statistical model."""

    # reporting function for model exploration and verification
    def report(self):
        pass

class TimeseriesWrapper:
    """Wrapper class for Timeseries and HistoricalTS.

    The Timeseries wrapper class is the encapsulation of the value-computing
    part and historical values. It contains the value-computing object
    (Timeseries at the moment) and historical values (HistoricalTS at the
    moment).

    """
    def __init__(self, ts, store_num =10000, **kwargs):
        self.timeseries = ts
        self.hxtimeseries = HistoricalTS(self.timeseries, store_num)

    def __getitem__(self, index):
        # this only works for ts with one Timeseries
        return self.hxtimeseries.retrieve(index)

    def __int__(self):
        return int(self.timeseries.value)

    def __float__(self):
        return float(self.timeseries.value)

    def __neg__(self):
        return -self.timeseries.value

    def __abs__(self):
        return abs(self.timeseries.value)

    def __str__(self):
        return str(self.timeseries.value)

    def __repr__(self):
        return str(self.timeseries.value)

    def __bool__(self):
        return bool(self.timeseries.value)

    def __hash__(self):
        return id(self)

    def __eq__(self, other):
        return self.timeseries.value == other

    def __ne__(self, other):
        return self.timeseries.value != other

    def __lt__(self, other):
        return self.timeseries.value < other

    def __gt__(self, other):
        return self.timeseries.value > other

    def __le__(self, other):
        return self.timeseries.value <= other

    def __ge__(self, other):
        return self.timeseries.value >= other

    def __add__(self, other):
        return self.timeseries.value + other

    def __sub__(self, other):
        return self.timeseries.value - other

    def __mul__(self, other):
        return self.timeseries.value * other

    def __truediv__(self, other):
        return self.timeseries.value / other

    def __floordiv__(self, other):
        return self.timeseries.value // other

    def __divmod__(self, other):
        return divmod(self.timeseries.value, other)

    def __mod__(self, other):
        return self.timeseries.value % other

    def __pow__(self, other):
        return self.timeseries.value ** other

    def __radd__(self, other):
        return other + self.timeseries.value

    def __rsub__(self, other):
        return other - self.timeseries.value

    def __rmul__(self, other):
        return other * self.timeseries.value

    def __rtruediv__(self, other):
        return other / self.timeseries.value

    def __rfloordiv__(self, other):
        return other // self.timeseries.value

    def __rdivmod__(self, other):
        return divmod(other, self.timeseries.value)

    def __rmod__(self, other):
        return other % self.timeseries.value

    def __rpow__(self, other):
        return other ** self.timeseries.value

class Timeseries:
    """Base class for time series.

    TimeSeries object should only concern about the updating of its series upon arrival of tick or
    candle and no more. The calculation part of the class should only hold the most updated
    value of the corresponding TimeSeries. The handling of the historical data would
    be designed and implemented in a later stage. Any cached data that the TimeSeries
    object maintained should not be accessed by other objects for any external purpose.

    Ordinary timeseries class is designed to be both an observable and an observer.
    This means that each instance of a Timeseries class has corresponding publisher/subscriber
    functionality that allows it to broadcast its changes to Timeseries that are listening
    to its updates/listen to updates from other timeseries.

    Args:
        ts   = Timeseries object to subscribe (or not rely on a TS if not specified)
        name = User given name of the Timeseries object (or the class name if not specified)

    For every Timeseries type object, the __init__ constructor of that type should first call
    super().__init__(ts=ts) or suitable base class constructor to initialize the
    observer-observable behaviour properly.

    """

    #Note that some particular Timseries object (e.g. CandleStick) has no observable to keep track of.
    #Rather, they act as a source of data for other types of Timeseries objects to listen to. Hence,
    #for CandleStick (or other source Timeseries), their data source should be constructed by an Event
    #via the Event bus architecture.

    #Any timeseries type should also support list-based initialization and update. The implementation
    #is deferred to a later stage due to prioritization of tasks.

    def __init__(self, ts=None):
        # self.subscribers are the list of references to timeseries objects that this instance subscribes to
        self.subscribers = []
        # self.subscribers_broadcasted is the set of timeseries that broadcasted previously
        self.subscribers_broadcasted = set()
        # self.listeners is the list of references to timeseries objects that listen to this timeseries
        self.listeners = []

        # ts is either a single ts object, or list containing multiple ts objects
        if ts is not None and not isinstance(ts, list):
            # for single ts object
            ts.listeners.append(self)
            self.subscribers.append(ts)
        elif ts is not None and isinstance(ts, list):
            # for a list containing multiple ts objects
            for t in ts:
                t.listeners.append(self)
                self.subscribers.append(t)

    def __float__(self):
        try:
            float(self.value)
            return float(self.value)
        except:
            return None

    # should implement for every child class of Timeseries
    def evaluate(self):
        raise NotImplementedError

    # by default, a listener would update only after all its subscribers updated once
    def processBroadcast(self, pos):
        if len(self.subscribers) == 1:
            self.update()
        else:
            self.subscribers_broadcasted.add(self.subscribers[pos])
            if len(self.subscribers_broadcasted) < len(self.subscribers):
                pass
            else:
                self.subscribers_broadcasted.clear()
                self.update()

    def update(self):
        # by current design, all evaluate of listeners would be called if candle decides to broadcast
        self.evaluate()

    # this calls all the processBroadcast methods of the instances which subscribe to the root timeseries
    def broadcast(self):
        # for list version of this paradigm
        # 1. find the index corresponds to the root instance in each listener.subscribers
        # 2. pass the index to listener
        for listener in self.listeners:
            pos = listener.subscribers.index(self)
            listener.processBroadcast(pos)

    # currently not in use
    def register(self, new_ts):
        # this registers listener to the self.listeners dictionary
        self.listeners[new_ts.name] = new_ts
        #self.listners.append(new_ts)

    # currently not in use
    def unregister(self, ts):
        del self.listeners[ts.name]
        #self.listeners.pop(ts)

    # pseudo-decorator for maintainng valid main cache in any instance of any Timeseries object
    def cache(func):
        """Decorator function for any Timeseries to maintain its valid main cache for calculating its output value.

        The class method to be decorated should initialize self._cache as empty list. The class should also
        contain an attribute self._lookback for caching purpose.

        """
        def prune(lst, lookback):
            if len(lst) < lookback:
                return lst
            else:
                return lst[-lookback:]

        def wrapper(*args, **kwargs):
            # set alias self
            self = args[0]
            # a hack - args[0] must be "self"
            # if no self._cache in original ts, create one for it
            if '_cache' not in self.__dict__.keys():
                self._cache = []
            if isinstance(self._ts, list):
                # exception case handling - for CandleStick-like object
                if self._ts[-1] is None or isinstance(self._ts[-1], float):
                    self._cache.append(self._ts[-1])
                    self._cache = prune(self._cache, self._lookback)
                # handle the case when self._ts is a list of ts objects
                if isinstance(self._ts[-1], Timeseries):
                    zip(*self._cache)
                    try:
                        self._cache.append([float(ts) for ts in self._ts])
                    except:
                        pass
                    self._cache = prune(self._cache, self._lookback)
                    zip(*self._cache)

            elif isinstance(self._ts, Timeseries):
                # handle the case when self._ts is a ts object or when candlestick as underlying ts
                try:
                    self._cache.append(float(self._ts))
                except:
                    pass
                # consider disallow any direct sourcing from candlestick apart from direct object
                try:
                    if self.bar:
                        self._cache.pop()
                        self._cache.append(self._ts.accessBar())
                except:
                    pass
            self._cache = prune(self._cache, self._lookback)
            func(*args, **kwargs)
        return wrapper


    # psuedo-decorator for maintaining valid open, close, high, low caches in any instance of any base class
    def bar_cache(func):
        """Decorator function for any class to maintain valid open, close, high and low caches.

        The class method to be decorated should initialize self.o, self.c, self.h, self.l as
        empty lists. It should also contain an attribute self._lookback for caching purpose.

        """
        def wrapper(self, **kwargs):
            self.o.append(float(candle.o))
            self.c.append(float(candle.c))
            self.h.append(float(candle.h))
            self.l.append(float(candle.l))
            self.t = float(candle.t)

            if len(self.o) < self._lookback:
                return
            elif len(self.o) >= self._lookback:
                self.o = self.o[-self._lookback:]
                self.c = self.c[-self._lookback:]
                self.h = self.h[-self._lookback:]
                self.l = self.l[-self._lookback:]

            func(*args, **kwargs)
        return wrapper

    def importBars(self):
        """ import functionality to import well defined excel columns as Timeseries objects """
        raise NotImplementedError

    def __int__(self):
        return int(self.value)

    def __float__(self):
        return float(self.value)

    def __neg__(self):
        return -self.value

    def __abs__(self):
        return abs(self.value)

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return str(self.value)

    def __bool__(self):
        return bool(self.value)

    def __hash__(self):
        return id(self)

    def __eq__(self, other):
        return self.value == other

    def __ne__(self, other):
        return self.value != other

    def __lt__(self, other):
        return self.value < other

    def __gt__(self, other):
        return self.value > other

    def __le__(self, other):
        return self.value <= other

    def __ge__(self, other):
        return self.value >= other

    def __add__(self, other):
        return self.value + other

    def __sub__(self, other):
        return self.value - other

    def __mul__(self, other):
        return self.value * other

    def __truediv__(self, other):
        return self.value / other

    def __floordiv__(self, other):
        return self.value // other

    def __divmod__(self, other):
        return divmod(self.value, other)

    def __mod__(self, other):
        return self.value % other

    def __pow__(self, other):
        return self.value ** other

    def __radd__(self, other):
        return other + self.value

    def __rsub__(self, other):
        return other - self.value

    def __rmul__(self, other):
        return other * self.value

    def __rtruediv__(self, other):
        return other / self.value

    def __rfloordiv__(self, other):
        return other // self.value

    def __rdivmod__(self, other):
        return divmod(other, self.value)

    def __rmod__(self, other):
        return other % self.value

    def __rpow__(self, other):
        return other ** self.value

class GenericTS(Timeseries):
    """Generic Timeseries object for sub-timeseries held by wrapper Metric class

    Args:
        ts = timeseries to be listened to, evalute meethod is called whevener ts broadcasts
        lookback = same as Timeseries
        eval_func = a function implemeneted in Wrapper class, equivalent to the evaluate method in Timeseries
        args      = arguments required to pass into eval_func for proper evaluation of GenericTS value
    """
    def __init__(self, ts, name=None, lookback=None, eval_func=None, args=None):
        super().__init__(ts=ts)
        self._lookback  = lookback
        self._ts        = ts
        self._cache     = []
        self.eval_func = eval_func
        self.args      = args
        self.value      = None

    @Timeseries.cache
    def evaluate(self):
        # pass a function "eval_func" reference to GenericTS.evaluate to update its value
        #eval_func should be defined in wrapper class
        self.value = self.eval_func(*self.args)
        self.broadcast()

class HistoricalTS(Timeseries):
    """Providing methods for historical Timeseries data management, storage and
    handling retrieval

    """

    def __init__(self, ts, store_num = 10000):
        super().__init__(ts=ts)
        self._ts = ts
        self._lookback = store_num
        self._cache = []
        self.value = None
        self.flashed = False

    # write to disk
    def write(self):
    # this function should periodically write to disk
    # write to a file, the filename should be changes accorindgly
        filename = str(self._ts.__class__.__name__) + str(hash(id(self._ts))) + ".csv"
        if not self.flashed:
            with open(filename, 'w', newline='') as file:
                file.write("Beginning of new file: should record the running instance metainfo \n")
            self.flashed = True

        with open(filename, "a", newline='') as file:
            wr = csv.writer(file)
            wr.writerow(self._cache[:self._lookback])
        del self._cache[:self._lookback]

    # update historical cache based on updated value
    def prune(self, lst):
        if 2 * self._lookback >= len(self._cache):
            return lst
        else:
            self.write()
            return lst[-self._lookback-1:]

    def evaluate(self):
        # this function should update whenever a change in the ts is present
        if isinstance(self._ts, list):
            if self._ts[-1] is None or isinstance(self._ts[-1], float):
                self._cache.append(self._ts[-1])
            if isinstance(self._ts[-1], Timeseries):
                zip(*self._cache)
                try:
                    self._cache.append([float(ts) for ts in self._ts])
                except:
                    pass
                zip(*self._cache)
        elif isinstance(self._ts, Timeseries):
            try:
                self._cache.append(float(self._ts))
            except:
                pass
        self._cache = self.prune(self._cache)

        if len(self._cache) > 0:
            self.value = self._cache[-1]
        else:
            pass

    # index is a slice object enetered by user - only allows -xxx:-xx retrieval method
    def retrieve(self, index):
        # this function should return a list of value including start but excluding end
        # also, this function should be able to redirect retrieval request to own cache/disk memory

        # only support this shit currently
        #if index.end > 0 or index.start > 0:
        #    return ValueError('The slice object input for referencing historical value should be by
        #    negative integers (i.e. ts[-1000:-800] for the 200 values starting from 800 bars from
        #    now)')

        ## row counts from bottom to top (end to beginning)
        #rowstart = abs(index.start % self._lookback)
        #rowend   = abs(index.stop % self._lookback)
        ## col counts from right to left (end to beginning)
        #colstart = abs(index.start) - rowstart * self._lookback
        #colend   = abs(index.end) - rowed * self._lookback
        print('entering hxts retrieve')
        filename = str(self._ts.__class__.__name__) + str(hash(id(self._ts))) + ".csv"
        print('printing csv filename in hxts retrieve {}'.format(filename))
        print(index)
        lst = []
        if isinstance(index, slice):
            if abs(index.stop) < self._lookback and abs(index.start) < self._lookback:
                # if still within caching limit, retrieve from cache
                return self._cache[index]
            else:
                with open(filename, "r") as f:
                    reader = csv.reader(f, delimiter=',')
                    for i, row in enumerate(f):
                        if i == 0: pass
                        else:
                            row = [float(x) for x in row.rstrip('\n').split(',')]
                            lst += row
                    lst += self._cache
                return lst[index]

        elif isinstance(index, int):
            if abs(index) < self._lookback:
                return self._cache[index]
            else:
                with open(filename, "r") as f:
                    reader = csv.reader(f, delimiter=',')
                    for i, row in enumerate(f):
                        if i == 0: pass
                        else:
                            row = [float(x) for x in row.rstrip('\n').split(',')]
                            lst += row
                    lst += self._cache
                return lst[index]

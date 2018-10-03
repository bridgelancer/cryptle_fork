from functools import wraps

class Metric:
    '''Base class with common functions of single valued metrics'''

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
    '''Mutable candle stick with namedtuple-like API.'''

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
    ''' Base class for holding statistical model '''

    # reporting function for model exploration and verification
    def report(self):
        pass


class Timeseries:
    ''' Base class for times series that encapsulate current Candle and Metric objects.

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
    super().__init__(ts=ts, name=name) or suitable base class constructor to initialize the
    observer-observable behaviour properly.

    '''

    #Note that some particular Timseries object (e.g. CandleStick) has no observable to keep track of.
    #Rather, they act as a source of data for other types of Timeseries objects to listen to. Hence,
    #for CandleStick (or other source Timeseries), their data source should be constructed by an Event
    #via the Event bus architecture.

    #Any timeseries type should also support list-based initialization and update. The implementation
    #is deferred to a later stage due to prioritization of tasks.

    def __init__(self, ts=None, name=None):
    # self.subscribers are the dictionary of timeseries object that listen to this timeseries
    # instance
        self.subscribers = dict()
        self.subscribers_broadcasted = set()
        self.listeners   = dict()
        self.name = name or self.__class__.__name__

        # ts is either a single ts object, or list containing multiple ts objects
        if ts is not None and not isinstance(ts, list):
            ts.listeners[self.name]     = self
            self.subscribers[ts.name]   = ts
        elif ts is not None and isinstance(ts, list):
            for t in ts:
                t.listeners[self.name]    = self
                self.subscribers[t.name]  = t

    def __float__(self):
        try:
            float(self.value)
            return float(self.value)
        except:
            return None

    # should implement for every child class of Timeseries
    def evaluate(self):
        raise NotImplementedError

    def processBroadcast(self, ts_name):
        if len(self.subscribers) == 1:
            self.update()
        # by default, processBroadcast trigger self.update only if
        else:
            self.subscribers_broadcasted.add(ts_name)
            if len(self.subscribers_broadcasted) < len(self.subscribers):
                pass
            elif len(self.subscribers_broadcasted) == len(self.subscribers):
                self.subscribers_broadcasted.clear()
                self.update()


    def update(self):
        # currnetly, all evaluate of listeners would be called if candle decides to broadcast
        self.evaluate()

    # this calls all the update methods of the instances which subscribe to the root timeseries
    def broadcast(self, ts_name):
        for listener in self.listeners:
            self.listeners[listener].processBroadcast(self.name)

    # currently not in use
    def register(self, new_ts):
        # this registers listener to the self.listeners dictionary
        self.listeners[new_ts.name] = new_ts

    # currently not in use
    def unregister(self, ts):
        del self.listeners[ts.name]

    # pseudo-decorator for maintainng valid main cache in any instance of any Timeseries object
    def cache(func):
        '''Decorator function for any Timeseries to maintain its valid main cache for calculating its output value.

        The class method to be decorated should initialize self._cache as empty list. The class should also
        contain an attribute self._lookback for caching purpose.

        '''
        def prune(lst, lookback):
            if len(lst) < lookback:
                return lst
            else:
                return lst[-lookback:]
        # **TODO** handle the case of multiple underlying timeseries and the related caching issues
        def wrapper(*args, **kwargs):
            # set alias self
            self = args[0]
            # a hack - args[0] must be "self"
            # if no self._cache in original ts, create one for it
            if '_cache' not in self.__dict__.keys():
                self._cache = []
            if isinstance(self._ts, list):
                if self._ts[-1] is None or isinstance(self._ts[-1], float):
                    self._cache.append(self._ts[-1])
                    self._cache = prune(self._cache, self._lookback)
                if isinstance(self._ts[-1], Timeseries):
                    zip(*self._cache)
                    try:
                        self._cache.append([float(ts) for ts in self._ts])
                    except:
                        pass
                    self._cache = prune(self._cache, self._lookback)
                    zip(*self._cache)
            elif isinstance(self._ts, Timeseries):
                # handling single value cases
                try:
                    self._cache.append(float(self._ts))
                except:
                    pass
                self._cache = prune(self._cache, self._lookback)
            func(*args, **kwargs)
        return wrapper

    # psuedo-decorator for maintaining valid open, close, high, low caches in any instance of any base class
    def bar_cache(func):
        '''Decorator function for any class to maintain valid open, close, high and low caches.

        The class method to be decorated should initialize self.o, self.c, self.h, self.l as
        empty lists. It should also contain an attribute self._lookback for caching purpose.

        '''
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
        ''' import functionality to import well defined excel columns as Timeseries objects '''
        raise NotImplementedError

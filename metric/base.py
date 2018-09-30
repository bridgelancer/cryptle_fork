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

    '''
    def __float__(self):
        try:
            float(self.value)
            return float(self.value)
        except:
            pass

     # pseudo-decorator for maintainng valid main cache in any instance of any base class
    def cache(func):
        '''Decorator function for any Timeseries to maintain its valid main cache for calculating its output value.

        The class method to be decorated should initialize self._cache as empty list. It should also
        contain an attribute self._lookback for caching purpose.

        '''
        def wrapper(*args, **kwargs):
            # if no self._cache in original ts, create one for it
            if '_cache' not in args[0].__dict__.keys():
                args[0]._cache = []

            try: # handling single value cases
                args[0]._cache.append(float(args[0]._ts))
            except: # handling bar cases
                args[0]._cache.append(args[0]._ts)

            # the routines that handle the caching
            if len(args[0]._cache) < args[0]._lookback:
                return
            elif len(args[0]._cache) > args[0]._lookback:
                args[0]._cache = args[0]._cache[-args[0]._lookback:]
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

    def importBars(self, ):
        ''' import functionality to import well defined excel columns as Timeseries objects '''
        raise NotImplementedError

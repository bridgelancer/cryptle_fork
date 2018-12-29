"""
Base classes for time series data structures.  Warning -------
The class names :class:`TimeseriesWrapper`, :class:`Timeseries`, and :class:`HistoricalTS` are
temporary and are subject to change.
"""
# Todo(pine): Refactor observer pattern into reusable set of mixins. (observe for a longer period)
from functools import wraps

import logging
import csv
import os
import datetime


class Metric:
    """Mixin class that provides dunder methods for of data objects witha single value."""

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


class TimeseriesWrapper(Metric):
    """Wrapper class for Timeseries and HistoricalTS.

    This class encapsulated the computational part and history storage part of
    time series data containers. It contains the value-computing object
    (Timeseries at the moment) and historical data object (HistoricalTS at the
    moment).

    """

    def __init__(self, ts, store_num=10000, **kwargs):
        self.timeseries = ts
        self.hxtimeseries = HistoricalTS(self.timeseries, store_num)

    def __getitem__(self, index):
        """Wrapping the HistoricalTS and give access via usual sequence syntax."""
        # this only works for ts with one Timeseries
        return self.hxtimeseries.__getitem__(index)

    @property
    def value(self):
        """ Returning the value of underlying ts and set it as an instance attribute of the
        wrapper."""
        return self.timeseries.value

    def __hash__(self):
        return id(self)


class Timeseries(Metric):
    """Container for time series data.

    TimeSeries object should only concern about the updating of its series upon arrival of tick or
    candle and no more. The calculation part of the class should only hold the most updated
    Any cached data that the TimeSeries object maintained should not be accessed by other objects
    for any external purpose.

    Ordinary Timeseries class is designed to be both an observable and an observer.
    This means that each instance of a Timeseries class has corresponding publisher/subscriber
    functionality that allows it to broadcast its changes to Timeseries that are listening
    to its updates/listen to updates from other timeseries.

    Upstream Timeseries (e.g. a :class:`~cryptle.metric.timeseries.candle.CandleStick`) is designed
    to only be an observable but not a observer. They act as a receptor for external data sources
    and should not depend on other Timeseries object for their updating of values.

    Args
    ----
    *vargs : :class:`~cryptle.metric.base.Timeseries`(s)
        One or more Timeseries objects to subscribe to

    """

    # Todo (MC):
    # Any timeseries type should also support list-based initialization and update

    def __init__(self, *vargs):
        self.name = None

        # self.subscribers are the list of references to timeseries objects that this instance subscribes to
        self.subscribers = []

        # self.subscribers_broadcasted is the set of timeseries that broadcasted previously
        self.subscribers_broadcasted = set()

        # self.listeners is the list of references to timeseries objects that listen to this timeseries
        self.listeners = []

        for arg in vargs:
            if isinstance(arg, Timeseries):
                arg.listeners.append(self)
                self.subscribers.append(arg)

    # ???Todo(pine): Determine how to handle function arguments
    def evaluate(self):
        """Virtual method to be implemented for each child instance of Timeseires"""
        raise NotImplementedError(
            "Please implement an evaluate method for every Timeseries instance"
        )

    def processBroadcast(self, pos):
        """To be called when all the listened Timeseries updated at least once."""
        if len(self.subscribers) == 1:
            self.update()
        else:
            self.subscribers_broadcasted.add(self.subscribers[pos])
            if len(self.subscribers_broadcasted) < len(self.subscribers):
                pass
            else:
                self.subscribers_broadcasted.clear()
                self.update()

    # ???Todo(pine): This should take arguments, requiring subclasses to know the internals of the
    # observables defeats the purpose of having this interface
    def update(self):
        """Wrapper interface for controlling the updating behaviour when there is new update."""
        # by current design, all evaluate of listeners would be called if candle decides to broadcast
        self.evaluate()

    def broadcast(self):
        """Call :meth:`processBroadcast` of all listeners."""
        # for list version of this paradigm
        # 1. find the index corresponds to the root instance in each listener.subscribers
        # 2. pass the index to listener
        for listener in self.listeners:
            pos = [id(x) for x in listener.subscribers].index(id(self))
            listener.processBroadcast(pos)

    def register(self, new_ts):
        """Registers another :class:`Timeseries` object as a listener."""
        self.listeners[new_ts.name] = new_ts
        # self.listners.append(new_ts)

    def unregister(self, ts):
        """Unregister the provided listener."""
        del self.listeners[ts.name]
        # self.listeners.pop(ts)

    @staticmethod
    def prune(arg, lookback=None):
        """The Timeseries class prune method (as opposed to the HistoricalTS one)."""
        if lookback is None:
            lookback = arg._lookback

        if len(arg._cache) < lookback:
            return arg._cache
        else:
            return arg._cache[-lookback:]

    @staticmethod
    def cache(prune):
        """Decorator for any Timeseries method to maintain its valid cache
        for calculating its output value.

        The class method to be decorated should initialize self._cache as empty
        list. The class should also contain a private attribute ``._lookback`` for
        caching purpose.

        Args
        ----
        prune_type: str
            Positional argument to decorator function, either 'normal' or 'historical'

        """

        def with_prune_type(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # set alias self
                # a hack - args[0] must be "self"
                self = args[0]
                if prune is "normal":
                    prune_type = Timeseries.prune
                elif prune == "historical":
                    prune_type = HistoricalTS.prune

                # if no self._cache in original ts, create one for it
                if "_cache" not in self.__dict__.keys():
                    self._cache = []

                if isinstance(self._ts, Timeseries):
                    if self._ts.value is not None:
                        self._cache.append(float(self._ts))
                if isinstance(self._ts, tuple):
                    buffer = []
                    for ts in self._ts:
                        if isinstance(ts, list):
                            pass
                        if isinstance(ts, Timeseries):
                            if ts.value is not None:
                                buffer.append(ts.value)

                    if len(buffer) == 1:
                        self._cache.append(self._ts[0].value)
                    elif len(buffer) > 1:
                        self._cache.append(buffer)

                self._cache = prune_type(self)
                func(*args, **kwargs)

            return wrapper

        return with_prune_type

    def importBars(self):
        """ Import functionality to import well defined excel columns as Timeseries objects """
        raise NotImplementedError

    def __hash__(self):
        """ Let :class:`Timeseries` be usable as dict keys, ignoring the object state."""
        return id(self)


class GenericTS(Timeseries):
    """Generic Timeseries object for sub-timeseries held by wrapper Metric class

    Args
    ----
    ts : :class:`cryptle.metric.base.Timeseries`
        One or more ``Timeseries`` to be listened to, evaluate method is called whever ts broadcasts
    lookback : int
        Same as :class:`~cryptle.metric.base.Timeseries`
    eval_func : function
        A function implemented in the wrapping :class:`~cryptle.metric.base.Timeseries` class, equivalent to
        the evalutate method of the ``Timeseries``
    args : list
        A list of arguments to be passed into the :meth:`eval_func` of
        :class:`~cryptle.metric.base.GenericTS` value1
    tocache : boolean, optional
        Parameter for determining whether to use the :meth:`~cryptle.metric.base.Timeseries.cache`
        decorator, False by default
    name : boolean, optional
        For easy referencing of GenericTS instance when necessary

    """

    def __init__(
        self, *ts, name=None, lookback=None, eval_func=None, args=None, tocache=True
    ):
        super().__init__(*ts)
        self.name = name
        self._lookback = lookback
        self._ts = ts
        self._cache = []
        self.eval_func = eval_func
        self.args = args
        self.tocache = tocache
        self.value = None

    def evaluate(self):
        if self.tocache:
            self.eval_with_cache()
        else:
            self.eval_without_cache()

    @Timeseries.cache("normal")
    def eval_with_cache(self):
        """Use when caching is needed."""
        self.value = self.eval_func(*self.args)
        self.broadcast()

    def eval_without_cache(self):
        """Use when caching is not needed."""
        self.value = self.eval_func(*self.args)
        self.broadcast()


class HistoricalTS(Timeseries):
    """Base class for management, storage, and retrieval of historical :class:`Timeseries` data.

    The current design of the storage of generated historical values is stored to directory named
    "histlog", in which the timestamp of the stamp of the first generated file during that execution
    would be used as the subdirectory name. Indiviudal historical timeseries values would be stored
    within a file under their respective class name and hash id to ensure uniqueness.

    Args
    ----
    ts : :class:`~cryptle.metric.base.Timeseries`
        The ``Timeseries`` to be stored and retrievable during runtime and in the future.
    store_num : int, optional
        The number of values to be cached during runtime before writing to disk.

    """

    def __init__(self, ts, store_num=10000):
        super().__init__(ts)
        self._ts = ts
        self._lookback = store_num
        self._cache = []
        self.value = None
        self.flashed = False

        # Setting up correct directory structure
        current_time = datetime.datetime.now()
        current_time_f = current_time.strftime("%Y-%m-%d %H:%M:%S")
        subdirpath = os.path.join("histlog", current_time_f)

        dirpath = os.path.join(
            os.getcwd(), subdirpath
        )  # relative pathing to the execution

        self.dir = dirpath
        self.dirpaths = []

        # Some leniency to let all files fall into same folder
        for i in range(-3, 3):
            diff_time = current_time + datetime.timedelta(seconds=i)
            diff_time_f = diff_time.strftime("%Y-%m-%d %H:%M:%S")
            subdirpath = os.path.join("histlog", diff_time_f)
            self.dirpaths.append(os.path.join(os.getcwd(), subdirpath))

    def write(self, num_to_write):
        """Write stored data to disk.

        The behaviour of this function is that the filename changes accorind to the has of the id of
        the Timeseries object to be written.

        """

        try:
            if all(not os.path.exists(dirpath) for dirpath in self.dirpaths):
                os.makedirs(self.dir)
                os.chdir(self.dir)
            else:
                os.chdir(self.dir)
        except Exception as e:
            raise OSError(
                "Error in creating the required directory for storing HistoricalTS values."
            )

        filename = str(self._ts.__class__.__name__) + str(hash(id(self._ts))) + ".csv"
        if not self.flashed:
            with open(filename, "w", newline="") as file:
                file.write(
                    "Beginning of new file: should record the running instance metainfo \n"
                )
            self.flashed = True

        with open(filename, "a", newline="") as file:
            wr = csv.writer(file)
            wr.writerow(self._cache[:num_to_write])

        os.chdir(os.path.dirname(os.path.dirname(os.getcwd())))

    @staticmethod
    def prune(self):
        """HistoricalTS class prune method. Write cache to disk and delete them from main memory."""
        if 2 * self._lookback >= len(self._cache):
            return self._cache
        else:
            self.write(self._lookback)
            del self._cache[: self._lookback]
            return self._cache[-self._lookback - 1 :]

    @Timeseries.cache("historical")
    def evaluate(self):
        """Caching handled by the cache decorator and class prune method"""
        if len(self._cache) > 0:
            self.value = self._cache[-1]
        else:
            pass

    # Todo(MC): To make this more smart in getting the required values
    @staticmethod
    def readCSV(cache, filename):
        """Helper function to return a list of usable values from pre-formatted csv file.

        Currently, this function non-selectively read the whole csv and reconstruct a python list.
        This is not the desired behaviour. It is designed to be only retrieve a suitable and
        reasonable amount of data from disk via some algorithm.

        Args
        ---
        cache : list
            Residual cache maintained on the fly
        filename: string
            Name of the csv file containing the data

        Returns
        -------
        lst[index]: list
            List of requested values.

        """
        lst = []
        with open(filename, "r") as f:
            reader = csv.reader(f, delimiter=",")
            for i, row in enumerate(f):
                if i == 0:
                    pass
                else:
                    row = [float(x) for x in row.rstrip("\n").split(",")]
                    lst += row
            lst += cache
        return lst

    def __getitem__(self, index):
        """Get historical values.

        Args
        ----
        index : slice
            A slice object - only allows -xxx:-xx retrieval method

        Returns
        -------
        lst[index]: list
            List of requested values.

        """
        # only support this currently
        # if index.end > 0 or index.start > 0:
        #    return ValueError('The slice object input for referencing historical value should be by
        #    negative integers (i.e. ts[-1000:-800] for the 200 values starting from 800 bars from
        #    now)')

        ## row counts from bottom to top (end to beginning)
        # rowstart = abs(index.start % self._lookback)
        # rowend   = abs(index.stop % self._lookback)
        ## col counts from right to left (end to beginning)
        # colstart = abs(index.start) - rowstart * self._lookback
        # colend   = abs(index.end) - rowed * self._lookback

        filename = str(self._ts.__class__.__name__) + str(hash(id(self._ts))) + ".csv"
        filepath = os.path.join(self.dir, filename)

        if isinstance(index, slice):
            try:
                # for handling index cases with integer bounded intervals and steps i.e. [-4:-2]
                if (
                    abs(index.stop) < self._lookback
                    and abs(index.start) < self._lookback
                ):
                    # if still within caching limit, retrieve from cache
                    return self._cache[index]
            except TypeError:
                # for handling index cases without integer bounded intervals and steps i.e. [-2:]
                if index.stop is None and abs(index.start) < self._lookback:
                    # if still within caching limit, retrieve from cache
                    return self._cache[index]
                elif index.stop is None and abs(index.start) >= self._lookback:
                    # if not within caching limit, retrieve from file
                    lst = HistoricalTS.readCSV(self._cache, filepath)
                    return lst[index]
            else:
                lst = HistoricalTS.readCSV(self._cache, filepath)
                return lst[index]

        elif isinstance(index, int):
            # for handling index cases with single intenger only
            if abs(index) < self._lookback:
                return self._cache[index]
            else:
                lst = HistoricalTS.readCSV(self._cache, filepath)
                return lst[index]

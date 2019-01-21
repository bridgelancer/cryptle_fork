"""Base classes for time series data structures.

This module provides Timeseries and MultivariateTS as the primary objects for cascading
runtime updating data and calculate the respective valid values. These objects could be
recursively applied to another Timeseries or MultivariateTS.

Historical Timeseiries values are also accessible, with the feature of writing to disk
to prevent excessive memory usage during runtime.

"""
# Todo(pine): Refactor observer pattern into reusable set of mixins. (observe for a longer period)
from functools import wraps
from collections import OrderedDict

import cryptle.logging as logging
import csv
import os
from pathlib import Path
import datetime

logger = logging.getLogger(__name__)


class Metric:  # pylint: disable=no-member
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


# Todo (MC):
# Any timeseries type should also support list-based initialization and update
class Timeseries(Metric):
    """Container for time series data.

    Timeseries contains the necessary machinery for calculating and accessing current
    and historical Timeseries values.

    Ordinary Timeseries class is designed to be both an observable and an observer.
    This means that each instance of a Timeseries class has corresponding
    subscriber/publisher functionality that allows it to broadcast its changes to
    Timeseries that are listening to its updates/listen to updates from other
    timeseries.

    Some upstream Timeseries (e.g. a
    :class:`~cryptle.metric.timeseries.candle.CandleStick`) is designed to only be an
    observable but not a observer. They act as a receptor for external data sources and
    should not depend on other Timeseries object for their updating of values.

    Args
    ----
    *vargs : :class:`~cryptle.metric.base.Timeseries` or :class:`~cryptle.metric.base.MultivariateTS`
        One or more Timeseries/MultivariateTS objects to subscribe to

    """

    def __init__(self, *vargs, timestamp=None):
        self.mxtimeseries = MemoryTS(self)
        self.hxtimeseries = DiskTS(self, timestamp)
        self.value = None

        # self.publishers are the list of references to timeseries objects that this
        # instance subscribes to
        self.publishers = []

        # self.publishers_broadcasted is the set of timeseries that broadcasted
        # previously
        self.publishers_broadcasted = set()

        # self.subscribers is the list of references to timeseries objects that listen
        # to this timeseries
        self.subscribers = []

        # Subscribe and Listen to the appropriate body
        for arg in vargs:
            arg.subscribers.append(self)
            logger.info('\nSubscribe {} as a subscriber of {}', repr(self), repr(arg))
            self.publishers.append(arg)
            logger.info('Listen {} as a listener of {} \n', repr(arg), repr(self))

    def __getitem__(self, index):
        """Wrapping the DiskTS and give access via usual list-value getting syntax."""
        return self.hxtimeseries.__getitem__(index)

    def evaluate(self):
        """Virtual method to be implemented for each child instance of Timeseires"""
        raise NotImplementedError(
            "Please implement an evaluate method for every Timeseries instance."
        )

    # Todo(MC): Unintended behaviour of broadcasts for mismatched updates
    def processBroadcast(self, pos):
        """To be called when all the listened Timeseries updated at least once."""
        if len(self.publishers) == 1:
            logger.debug(
                'Obj: {}. All publisher broadcasted, proceed to updating', repr(self)
            )
            self.update()
        else:
            self.publishers_broadcasted.add(self.publishers[pos])
            if len(self.publishers_broadcasted) < len(self.publishers):
                logger.debug(
                    'Obj: {}. Number of publisher broadcasted: {}',
                    repr(self),
                    len(self.publishers_broadcasted),
                )
                logger.debug(
                    'Obj: {}. Number of publisher remaining: {}',
                    repr(self),
                    len(self.publishers) - len(self.publishers_broadcasted),
                )
            else:
                self.publishers_broadcasted.clear()
                self.update()
                logger.debug(
                    'Obj: {}. All publisher broadcasted, proceed to updating',
                    repr(self),
                )

    def update(self):
        """Wrapper interface for controlling the updating behaviour when there is new
        update."""
        logger.debug(
            'Obj: {}. Calling evaluate method of the respective Timeseries', repr(self)
        )

        # the child :meth:``evaluate`` method either returns None (for Timeseries), or
        # 'source'/'generic'/'NA' (for GenericTS)
        string = self.evaluate()
        if string != 'source' and string != 'NA':
            # By current design, all :meth:`evaluate` of subscribers would be called if
            # candle decides to broadcast
            self.hxtimeseries.evaluate()
            self.broadcast()

        # The :meth:`evaluate` of hxtimeseries would also be called by default, could
        # modify this behaviour in the future

        # This introduces a buggy behaviour - as self.hxtimeseries.evaluate is called later than any
        # of the listener, at the end of the broadcastin cascade this will result in in completing
        # caching of values.

    def broadcast(self):
        """Call :meth:`~processBroadcast` of all subscribers."""
        # for list version of this paradigm
        # 1. find the index corresponds to the root instance in each
        #    subscriber.publishers
        # 2. pass the index to subscriber
        for subscriber in self.subscribers:
            pos = [id(x) for x in subscriber.publishers].index(id(self))
            logger.debug(
                'Obj: {}, Calling processBroadcast of subscriber {}',
                repr(self),
                type(subscriber),
            )
            subscriber.processBroadcast(pos)

    def subscribe(self, new_ts):
        """Registers another :class:`~Timeseries` object as a subscriber."""
        logger.info('Obj: {}, registering {} as a subscriber', self, new_ts)
        self.subscribers.append(new_ts)

    def unsubscribe(self, ts_to_remove):
        """Unregister an existing subscriber."""
        logger.info('Obj: {}, unregistering {} as a subscriber', self, ts)
        # to be implemented

    def listen(self, new_ts):
        """Registers another :class:`~Timeseries` object as a subscriber."""
        logger.info('Obj: {}, registering {} as a listener', self, new_ts)
        self.listeners.append(new_ts)

    def unlisten(self, ts_to_remove):
        """Unregister an existing subscriber."""
        logger.info('Obj: {}, unregistering {} as a listener', self, ts)
        # to be implemented

    def importBars(self):
        """ Import functionality to import well defined excel columns as Timeseries
        objects """
        raise NotImplementedError

    def __hash__(self):
        """ Let :class:`~Timeseries` be usable as dict keys, ignoring the object
        state."""
        return id(self)

    def getSubscribers(self):
        return self.subscribers

    def getListeners(self):
        return self.listeners

class MultivariateTS:
    """Wrapper for objects holding multiple Timeseries objects

    MultivariateTS provides integrating facilities for objects that hold multiple
    Timeseries object to interface with the publisher-subscriber interface at ease.

    Without the use of MultivariateTS, any objects subclassed from Timeseries that would
    wish to listen to all the Timeseries objects held by a particular wrapping construct
    would have to reference back to the module defining that wrapping construct, and
    write correspondingly. This makes room for errors and inadverent use of the wrapping
    construct in place of the intended Timeseries.

    Therefore, any object that intends to hold several Timeseries and is not a
    Timeseries itself should subclass from MultivariateTS.

    In the future, integration tests would be developed at the strategy level to check
    whether the Timeseries/TSwrapper intialized by the user code (the implemented
    strategy module).

    Args
    ----
    *vargs : :class:`~cryptle.metric.base.Timeseries` or :class:`~cryptle.metric.base.MultivariateTS`
        One or more Timeseries/MultivariateTS objects to subscribe to
    """

    def __init__(self, *vargs):
        self.subscribers = []
        self.publishers = []
        self.publishers_broadcasted = set()

        for arg in vargs:
            arg.subscribers.append(self)
            self.publishers.append(arg)

    def get_generic_ts(self):
        """Return a list of the GenericTS within the wrapper, sorted by the alphabetical
        order of their key names"""

        lst_ts = []
        for name, obj in OrderedDict(
            sorted(self.__dict__.items(), key=lambda t: str.lower(t[0]))
        ).items():
            if isinstance(obj, Timeseries):
                lst_ts.append(obj)
        return lst_ts

    def broadcast(self):
        """Duck-typed with the :meth:`~cryptle.metric.base.Timeseries.broadcast`"""
        pass

    def processBroadcast(self, pos):
        """Duck-typed with the :meth:`~cryptle.metric.base.Timeseries.processBroadcast`"""
        pass

    # Duck-typing
    broadcast = Timeseries.broadcast
    processBroadcast = Timeseries.processBroadcast

    def update(self):
        """Call the class evaluate and broadcast method"""
        self.evaluate()
        self.broadcast()

    def evaluate(self):
        """Virtual method to be implemented for each child instance of Timeseires"""
        raise NotImplementedError(
            "Please implement an evaluate method for every MultivariateTS instance."
        )


class MemoryTS(Metric):
    def __init__(self, ts):
        self._ts = ts

    @staticmethod
    def prune(arg, lookback=None):
        """The MemoryTS class prune method (as opposed to the DiskTS one)."""
        if lookback is None:
            lookback = arg._lookback

        if len(arg._cache) < lookback:
            return arg._cache
        else:
            return arg._cache[-lookback:]

    @staticmethod
    def cache(prune):
        """Decorator for any :meth:`evaluate` to maintain its valid cache for
        calculating its output value.

        The class method to be decorated should initialize self._cache as empty list.
        The class should also contain a private attribute ``._lookback`` for caching
        purpose.

        It handles the cachine of possible types being pased into ``self._ts`` of a Timeseries.

        Args
        ----
        prune_type: str
            Argument to specify the prune function to be used, either 'normal' or
            'historical'. Use 'normal' for developing new Timeseries.

        """

        def with_prune_type(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # set alias self - hacking interface
                self = args[0]

                if prune is 'normal':
                    prune_type = MemoryTS.prune
                elif prune == 'historical':
                    prune_type = DiskTS.prune

                if isinstance(self._ts, Timeseries):
                    if self._ts.value is not None:
                        self._cache.append(float(self._ts))

                elif isinstance(self._ts, tuple):
                    buffer = []
                    ts_count = 0
                    for ts in self._ts:
                        if isinstance(ts, list):
                            pass
                        if isinstance(ts, Timeseries):
                            if ts.value is not None:
                                buffer.append(ts.value)
                            ts_count += 1
                        if isinstance(ts, MultivariateTS):
                            lst_ts = ts.get_generic_ts()
                            for t in lst_ts:
                                if t.value is not None:
                                    buffer.append(t.value)
                            ts_count += len(lst_ts)

                    # should be the sum of tsl, including those in MultivariateTS
                    if len(buffer) != ts_count:
                        val = func(*args, **kwargs)
                        return val
                    else:
                        if len(buffer) == 1:
                            self._cache.append(self._ts[0].value)
                        elif len(buffer) > 1:
                            self._cache.append(buffer)

                elif isinstance(self._ts, MultivariateTS):
                    lst_ts = self._ts.get_generic_ts()
                    buffer = []
                    for ts in lst_ts:
                        if ts.value is not None:
                            buffer.append(ts.value)
                    self._cache.append(buffer)

                self._cache = prune_type(self)
                val = func(*args, **kwargs)
                return val

            return wrapper

        return with_prune_type


class GenericTS(Timeseries):
    """Generic Timeseries object for sub-timeseries held by a MultivariateTS or any wrapper object

    Args
    ----
    ts : :class:`~cryptle.metric.base.Timeseries` or :class:`~cryptle.metric.base.MultivariateTS`
        One or more ``Timeseries`` or ``MultivariateTS`` to be listened to, evaluate method is called whever
        ts broadcasts
    lookback : int
        Same as :class:`~cryptle.metric.base.Timeseries`
    eval_func : function
        A function implemented in the __init__ method of the wrapping
        class, equivalent to the evalutate method of the ``Timeseries``
    args : list
        A list of arguments to be passed into the :meth:`eval_func` of
        :class:`~cryptle.metric.base.GenericTS` value
    tocache : boolean, optional
        Parameter for determining whether to use the
        :meth:`~cryptle.metric.base.Timeseries.cache` decorator, False by default
    name : boolean, optional
        For easy referencing of GenericTS instance when necessary

    """

    def __repr__(self):
        if self.name is None:
            return 'GenericTS'
        else:
            return self.name

    def __init__(
        self,
        *vargs,
        name=None,
        lookback=None,
        eval_func=None,
        args=None,
        tocache=True,
        timestamp=None,
    ):
        self.name = name
        super().__init__(*vargs, timestamp=timestamp)
        self._lookback = lookback
        self._ts = vargs
        self._cache = []
        self.eval_func = eval_func
        self.args = args
        self.tocache = tocache

    def evaluate(self):
        if self.tocache:
            string = self.eval_with_cache()
            return string
        else:
            string = self.eval_without_cache()
            return string

    @MemoryTS.cache("normal")
    def eval_with_cache(self):
        """Use when caching is needed."""
        val = self.eval_func(*self.args)
        if val is not None:
            self.value = val
            return 'generic'
        else:
            return 'NA'

    def eval_without_cache(self):
        """Use when caching is not needed."""
        self.value = self.eval_func(*self.args)
        self.broadcast()
        return 'source'


class DiskTS(Metric):
    """Class for management, storage, and retrieval of historical :class:`Timeseries`
    data.

    The current design of the storage of generated historical values is stored to
    directory named "histlog", in which the timestamp of the stamp of the first
    generated file during that execution would be used as the subdirectory name.
    Indiviudal historical timeseries values would be stored within a file under their
    respective class name and hash id to ensure uniqueness.

    Args
    ----
    ts : :class:`~cryptle.metric.base.Timeseries`
        The ``Timeseries`` to be stored and retrievable during runtime
    store_num : int, optional
        The number of values to be cached during runtime before writing to disk.

    """

    def __init__(self, ts, timestamp=None, store_num=100):
        # Handle the case of writing timestamp
        if timestamp is None:
            self._ts = ts
        else:
            if isinstance(timestamp, Timeseries):
                self._ts = timestamp, ts

        self._store_num = store_num
        self._cache = []
        self.value = None
        self.flashed = False

        # Setting up correct directory structure
        current_time = datetime.datetime.now()
        current_time_f = current_time.strftime("%Y-%m-%d %H:%M:%S")

        histroot = Path('histlog')
        subdirpath = histroot / current_time_f

        # absolute pathing to the execution
        dirpath = Path.cwd() / subdirpath
        assert dirpath.is_absolute()

        self.dir = dirpath
        self.dirpaths = []

        # Some leniency to let all files fall into same folder
        for i in range(-3, 3):
            diff_time = current_time + datetime.timedelta(seconds=i)
            diff_time_f = diff_time.strftime("%Y-%m-%d %H:%M:%S")
            subdirpath = histroot / diff_time_f
            self.dirpaths.append(Path.cwd() / subdirpath)

    def cleanup(self):
        self.write(None)

    def cleanup(self):
        self.write(None)

    def write(self, num_to_write):
        """Write stored data to disk.

        The behaviour of this function is that the filename changes accorind to the has
        of the id of the Timeseries object to be written.

        """
        dpath = None
        try:
            if all([not Path.exists(dirpath) for dirpath in self.dirpaths]):
                os.makedirs(self.dir)
                dpath = self.dir
            else:
                for dirpath in self.dirpaths:
                    if Path.exists(dirpath):
                        dpath = dirpath
                        break
        except Exception as e:
            raise OSError(
                "Error in creating the required directory for storing DiskTS values."
            )

        filename = repr(self._ts) + '_' + str(hash(id(self._ts))) + ".csv"

        if not self.flashed:
            with open(dpath / filename, "w", newline="") as file:
                file.write(
                    "Beginning of new file: should record the running instance metainfo. \n"
                )
            self.flashed = True

        with open(dpath / filename, "a", newline="") as file:

            wr = csv.writer(file)
            if isinstance(self._ts, Timeseries):
                wr.writerow(self._cache[:num_to_write])
            elif isinstance(self._ts, tuple):
                for ts_with_time in self._cache:
                    wr.writerow(ts_with_time)

    @staticmethod
    def prune(self):
        """DiskTS class prune method. Write cache to disk and delete them from main
        memory."""
        if 2 * self._store_num >= len(self._cache):
            return self._cache
        else:
            self.write(self._store_num)
            del self._cache[: self._store_num]
            return self._cache[-self._store_num - 1 :]

    @MemoryTS.cache("historical")
    def evaluate(self):
        """Caching handled by the cache decorator and DiskTS class prune method"""
        if len(self._cache) > 0:
            self.value = self._cache[-1]
        else:
            pass

    # Todo(MC): To make this more smart in getting the required values
    @staticmethod
    def readCSV(cache, filename):
        """Helper function to return a list of usable values from pre-formatted csv
        file.

        Currently, this function non-selectively read the whole csv and reconstruct
        a python list.  This is not the desired behaviour. It is designed to be only
        retrieve a suitable and reasonable amount of data from disk via some
        algorithm.

        Args
        ---
        cache : list
            Residual cache maintained on the fly
        filename: string
            Name of the csv file containing the stored data

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
            A slice object - could handle all valid item retrieval syntax.

        Returns
        -------
        lst[index]: list
            List of requested values.

        """
        # row counts from bottom to top (end to beginning)
        # rowstart = abs(index.start % self._store_num)
        # rowend   = abs(index.stop % self._store_num)

        # col counts from right to left (end to beginning)
        # colstart = abs(index.start) - rowstart * self._store_num
        # colend   = abs(index.end) - rowed * self._store_num

        if isinstance(self._ts, Timeseries):
            filename = str(self._ts.name) + '_' + str(id(self._ts)) + '.csv'
        elif isinstance(self._ts, tuple):
            filename = str(self._ts[1].name) + '_' + str(id(self._ts[1])) + '.csv'
        filepath = os.path.join(self.dir, filename)

        if isinstance(index, slice):
            try:
                # for handling index cases with integer bounded intervals and steps i.e.
                # [-4:-2]
                if (
                    abs(index.stop) < self._store_num
                    and abs(index.start) < self._store_num
                ):
                    # if still within caching limit, retrieve from cache
                    return self._cache[index]
            except TypeError:
                # for handling index cases without integer bounded intervals and steps
                # i.e. [-2:]
                if index.stop is None and abs(index.start) < self._store_num:
                    # if still within caching limit, retrieve from cache
                    return self._cache[index]
                elif index.stop is None and abs(index.start) >= self._store_num:
                    # if not within caching limit, retrieve from file
                    lst = DiskTS.readCSV(self._cache, filepath)
                    return lst[index]
            else:
                lst = DiskTS.readCSV(self._cache, filepath)
                return lst[index]

        elif isinstance(index, int):
            # for handling index cases with single intenger only
            if abs(index) < self._store_num:
                return self._cache[index]
            else:
                lst = DiskTS.readCSV(self._cache, filepath)
                return lst[index]

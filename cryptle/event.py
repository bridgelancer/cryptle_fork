import inspect
import functools
from collections import defaultdict


class BusException(Exception):
    pass


class ExtraEmit(BusException):
    pass


class NotListenedWarning(BusException):
    pass


class UnboundEmitter(BusException):
    pass


class Bus:
    """Event bus middleware.

    This class allows wiring of function chains to be decoupled into events.

    """
    def __init__(self):
        self._callbacks = defaultdict(list)
        self._emitters  = defaultdict(list)

    def emit(self, event, data):
        """Directly emit events into the event bus."""

        if event not in self._callbacks:
            raise NotListenedWarning('No registered callbacks in this bus.')

        for cb in self._callbacks[event]:
            cb(data)

    def on(self, event, cb=None):
        """Decorator for event callbacks. Can also be used inline.

        Multiple events can be listened to, either with multiple decorating statement
        or as extra arguments a single decorate statment.
        """
        if cb:
            self.addCallback(event, cb)
        else:
            def decorator(cb):
                self.addCallback(event, cb)
                return cb
            return decorator

    def source(self, event):
        """Decorator for emitter function/methods.

        When the decorated method is binded to a bus, the functions's return value
        will be sent to the bus before being returned to the caller.

        A source can only emit one event. Multiple buses may be bounded to a source.
        When the source is called all binded buses will receive the event.

        Note:
            In use cases with multiple buses, the order that the buses receive the
            event is in order that they were binded. This is an implementation
            detail and is subject to change. Multi-thread usage is thus discouraged.
        """
        def decorator(method):
            wrapper = self.makeEmitter(event, method)
            return wrapper
        return decorator

    def addCallback(self, event, cb):
        """Register events directly into the event bus."""
        self._callbacks[event].append(cb)

    def addEmitter(self, event, cb):
        """Register emitter directly into the event bus."""
        self._emitters[event].append(cb)

    @staticmethod
    def makeEmitter(event, method):
        """Decorator for event emitting methods.

        If the object instance of the decorated method is binded to a bus, the
        return value will be sent to the bus before being returned. The method must
        therefore return only a single value.

        A method can only emit one event.
        """
        if getattr(method, '_emits', False):
            raise ExtraEmitError('An emitter may only emit one type of event.')

        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            rvalue = method(self, *args, **kwargs)
            meth = getattr(self, method.__name__)

            for bus in meth._buses:
                bus.emit(event, rvalue)

            return rvalue

        wrapper._emits = event
        wrapper._buses = []
        return wrapper

    def bind(self, object):
        """Binds an object or function and register decorated methods on the bus.

        Args:
            object: An object instance from a class with methods decorated as
              callback or emitters.

        Note:
            Functors will not be treated as functions.
        """
        no_decorated = True
        if inspect.isfunction(object):
            if hasattr(object, '_events'):
                for evt in object._events:
                    self.addCallback(evt, method)
                no_decorated = False

            if hasattr(object, '_emits'):
                object._buses.append(self)
                no_decorated = False

        # object likely is a class instance
        else:
            for _, attr in inspect.getmembers(object):
                if inspect.ismethod(attr):
                    method = attr

                    # Bind callbacks
                    if hasattr(method, '_events'):
                        for evt in method._events:
                            self.addCallback(evt, method)
                        no_decorated = False

                    # Bind emitters
                    if hasattr(method, '_emits'):
                        method._buses.append(self)
                        no_decorated = False

        if no_decorated:
            raise ValueError('Object {} has no callbacks or emitters.'.foramt(object))


def unbound_callback(*events):
    """Decorator for unbounded event callbacks.

    An unbounded callback must be binded to an event bus to be useful. Without
    a binding, the callback behaves just like a regular function.
    """
    def decorator(method):
        if hasattr(method, '_events'):
            method._events += events
        else:
            method._events = events
        return method
    return decorator


def unbound_source(event):
    """Decorator for unbound event emitting instance methods.

    An unbounded source must be binded to an event bus to be useful. Without
    a binding, the emitter behaves just like a regular function.
    """
    def decorator(method):
        if getattr(method, '_emits', False):
            raise ExtraEmitError('An emitter may only emit one type of event.')

        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            rvalue = method(self, *args, **kwargs)
            meth = getattr(self, method.__name__)

            for bus in meth._buses:
                bus.emit(event, rvalue)

            return rvalue

        wrapper._emits = event
        wrapper._buses = []
        return wrapper
    return decorator

def unbound_generic_source(event):
    """Decorator for unbound event emitting functions/static methods.

    An unbounded source must be binded to an event bus to be useful. Without
    a binding, the emitter behaves just like a regular function.
    """
    def decorator(method):
        if getattr(method, '_emits', False):
            raise ExtraEmitError('An emitter may only emit one type of event.')

        @functools.wraps(method)
        def wrapper(*args, **kwargs):
            rvalue = method(*args, **kwargs)

            for bus in method._buses:
                bus.emit(event, rvalue)

            return rvalue

        wrapper._emits = event
        wrapper._buses = []
        return wrapper

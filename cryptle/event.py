import inspect
import functools


class BusException(Exception):
    pass


class ExtraEmit(BusException):
    pass


class NotListenedWarning(BusException):
    pass


class UnboundedEmitter(BusException):
    pass


class NoRegisteredMethod(BusException):
    pass


class Bus:
    """Event bus middleware.

    This class allows wiring of function chains to be decoupled into events.

    """
    def __init__(self):
        self._callbacks = {}

    def on(self, evt, cb):
        """Register events directly into the event bus."""
        if evt not in self._callbacks:
            self._callbacks[evt] = []
        self._callbacks[evt].append(cb)

    def emit(self, evt, data):
        """Emit events directly into the event bus."""

        if evt not in self._callbacks:
            raise NotListenedWarning('No registered callbacks in this bus.')

        for cb in self._callbacks[evt]:
            cb(data)

    def bind(self, object):
        """Binds an object and register it's decorated methods on the bus.

        Args:
            object: An object instance from a class with methods decorated as
                callback or emitters.
        """
        no_decorated = True
        for _, attr in inspect.getmembers(object):
            if inspect.ismethod(attr):
                method = attr
                try:
                    for evt in method._events:
                        self.on(evt, method)
                except AttributeError:
                    pass
                else:
                    no_decorated = False

                # Common use case is binding instance to single bus
                # This optimise for performance
                if hasattr(method, '_emits'):
                    method._buses.append(self)
                    no_decorated = False

        if no_decorated:
            raise NoRegisteredMethod('Object {} has no callbacks or emitters.'.foramt(obj))


def on(*events):
    """Decorator to designate object methods as event callbacks.

    The decorated method must take a single argument for the event data.

    Multiple events can be listened to, either with multiple decorating statement
    or as extra arguments a single decorate statment.
    """
    def decorator(method):
        if hasattr(method, '_events'):
            method._events += events
        else:
            method._events = events
        return method
    return decorator


def emit(event):
    """Decorator for event emitting methods.

    If the object instance of the decorated method is binded to a bus, the
    return value will be sent to the bus before being returned. The method must
    therefore return only a single value.

    A method can only emit one event.
    """
    def decorator(method):
        if getattr(method, '_emits', False):
            raise ExtraEmitError('Only one event allowed for each method.')

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

import inspect
import functools


class LoopException(Exception):
    pass


class ExtraEmit(LoopException):
    pass


class NotListenedWarning(LoopException):
    pass


class UnboundedEmitter(LoopException):
    pass


class NoRegisteredMethod(LoopException):
    pass


class BaseLoop:
    def __init__(self):
        self._callbacks = {}

    def on(self, evt, cb):
        """Register events directly into the event loop."""
        if evt not in self._callbacks:
            self._callbacks[evt] = []
        self._callbacks[evt].append(cb)

    def emit(self, evt, data):
        """Emit events directly into the event loop."""

        if evt not in self._callbacks:
            raise NotListenedWarning('No registered callbacks in this loop.')

        for cb in self._callbacks[evt]:
            cb(data)


class Loop(BaseLoop):
    """Event loop middleware."""

    def bind(self, obj):
        """Binds an obj object and register it's decorated methods in the loop.

        Args:
            obj: An instance from a class with methods decorated as callback or
                emitters.
        """
        no_decorated = True
        for _, attr in inspect.getmembers(obj):
            if inspect.ismethod(attr):
                method = attr
                try:
                    for evt in method._events:
                        self.on(evt, method)
                except AttributeError:
                    pass
                else:
                    no_decorated = False

                # Common use case is binding instance to single loop
                # This optimise for performance
                if hasattr(method, '_emits'):
                    method._loops.append(self)
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

    If the object instance of the decorated method is binded to a loop, the
    return value will be sent to the loop before being returned. The method must
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

            # Bounded to an event loop instance
            try:
                loops = meth._loops
            except AttributeError:
                # Todo: add setting to raise warning
                loops = []

            for loop in loops:
                loop.emit(event, rvalue)

            return rvalue

        wrapper._emits = event
        wrapper._loops = []
        return wrapper
    return decorator

import inspect
import functools


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
            # @todo logging warn null callbacks
            # @todo create user defined warning
            raise Warning('No callbacks for event')
            return
        for cb in self._callbacks[evt]:
            cb(data)


class Loop(BaseLoop):
    """Basic event loop."""
    def bind(self, instance):
        """Binds an instance object and register it's decorated methods in the loop.
        """
        for _, attr in inspect.getmembers(instance):
            if inspect.ismethod(attr):
                meth = attr
                if getattr(meth, '_iscallback', False):
                    self.on(meth._event, meth)
                if getattr(meth, '_isemitter', False):
                    instance._loop = self


def on(event):
    """Decorator to designate object methods as event callbacks.

    The decorated method must take a single argument for the event data.
    """
    def decorator(method):
        method._iscallback = True
        method._event = event
        return method
    return decorator


def emit(event):
    """Decorator for event emitting methods.

    If the object instance of the decorated method is binded to a loop, the
    return value will be sent to the loop before being returned. The method must
    therefore return only a single value.
    """
    def decorator(method):
        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            rvalue = method(self, *args, **kwargs)

            # Bounded to an event loop instance
            if getattr(self, '_loop', False):
                self._loop.emit(event, rvalue)

            return rvalue

        wrapper._isemitter = True
        wrapper._event = event
        return wrapper
    return decorator

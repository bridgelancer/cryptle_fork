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
    def bind(self, instance):
        for _, attr in inspect.getmembers(instance):
            if inspect.ismethod(attr):
                meth = attr
                if getattr(meth, '_iscallback', False):
                    self.on(meth._event, meth)
                if getattr(meth, '_isemitter', False):
                    instance._loop = self


def on(event):
    """Method decorator for class methods designed to be used in an event loop.
    """
    def decorator(method):
        method._iscallback = True
        method._event = event
        return method
    return decorator


def emit(event):
    def decorator(method):
        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            # Unbounded
            if getattr(self, '_loop', False):
                self._loop.emit(event, method(self, *args, **kwargs))
            # Bounded to an event loop instance
            else:
                return method(self, *args, **kwargs)

        wrapper._isemitter = True
        wrapper._event = event
        return wrapper
    return decorator

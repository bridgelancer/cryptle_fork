import functools
import inspect


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


class NullLoop(BaseLoop):
    pass


class Loop(BaseLoop):
    def bind(self, obj):
        if not isinstance(obj, Listener):
            raise TypeError('Object must be an instance of Listener.')

        loop = obj.loop
        if not isinstance(loop, Loop):
            self._transfer(loop)
            obj.loop = self
        # @Todo Emitter instances

    def _transfer(self, loop):
        for evt in loop._callbacks:
            if evt not in self._callbacks:
                self._callbacks[evt] = loop._callbacks[evt]
            self._callbacks[evt] += loop._callbacks[evt]

# Todo consider metaclass
class Listener:
    """Abstract base classes for classes designed to work with event decorators.
    """
    def __init__(self, loop=None):
        self.loop = loop or NullLoop()


# Todo not working yet
def on(event):
    """Method decorator for class methods designed to be used in an event loop.
    """
    def decorator(method):
        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            self.on(event, method)
            method(self, *args, **kwargs)
        return wrapper
    return decorator


# Todo
class Emitter:
    pass


# Todo
def emit(event):
    pass

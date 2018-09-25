import inspect
import logging
from functools import wraps
from collections import defaultdict

_log = logging.getLogger(__name__)


class BusException(Exception):
    """Base exception for this module."""
    pass


class ExtraEmit(BusException):
    pass


class NotListened(BusException):
    pass


class UnboundEmitter(BusException):
    pass


class _Emitter:
    """Functor descriptor for wrapper functions and instance methods into bindable emitters."""
    def __init__(self, event, func):
        if isinstance(func, self.__class__):
            raise ExtraEmitError('An emitter may only emit one type of event.')
        self.func = func
        self.buses = []
        self.event = event
        self.instance = None

    def __repr__(self):
        return 'Emitter({}, {})'.format(self.event, self.func)

    def __get__(self, instance, owner=None):
        self.instance = instance
        return self

    def __call__(self, *args, **kwargs):
        if self.instance:
            rvalue = self.func(self.instance, *args, **kwargs)
        else:
            rvalue = self.func(*args, **kwargs)

        for bus in self.buses:
            bus.emit(self.event, rvalue)
        return rvalue


class Bus:
    """Event bus middleware.

    The purpose of an event bus is to decoupled hardcoded function chains into
    modular components that are agnostic about the implementation and existance
    of its dependency.
    """
    # Todo: Allow removal of callback/emitter bindings.
    def __init__(self):
        self._callbacks = defaultdict(list)
        self._emitters  = defaultdict(list)

    def bind(self, object):
        """Catch all method for binding objects, methods, or functions to the bus.

        Global functions or directly named instance methods will be bound as
        normal. Instance objects will be inspected, and methods decorated as
        source or callbacks will be bound.

        Args:
            object: The object to be bound/inspected.

        Note:
            Functors will not be treated as functions.
        """
        decorated = False

        if hasattr(object, '_events'):
            for evt in object._events:
                self.addListener(evt, object)
            decorated = True

        # global functions binded as emitters
        if isinstance(object, _Emitter):
            object.buses.append(self)
            decorated = True

        if isinstance(object, DeferedSource):
            object._bus = self
            decorated = True

        # object is instance variable, find unbound methods in the instance
        if inspect.isclass(object.__class__):
            for _, attr in inspect.getmembers(object):

                # bind callbacks
                if hasattr(attr, '_events'):
                    for evt in attr._events:
                        self.addListener(evt, attr)
                    decorated = True

                # bind emitters
                if isinstance(attr, _Emitter):
                    attr.buses.append(self)
                    decorated = True

        if not decorated:
            raise ValueError('Expected callbacks or emitters in {}.'.format(object))

    def emit(self, event, data):
        """Directly emit events into the event bus."""

        if event not in self._callbacks:
            pass
            #raise NotListened('No registered callbacks for "{}" in this bus.'.format(event))

        for cb in self._callbacks[event]:
            cb(data)

    def on(self, event):
        """Decorator for global functions as bound event callbacks.

        The same callback can listen to multiple events. Callbacks must take a
        single argument positional for the event data.

        Warning:
            Does not work on instance methods. This is because without the use
            of metaclasses, bound methods do not inherit the template function
            of a class.
        """
        def decorator(func):
            self.addListener(event, func)
            return func
        return decorator

    def source(self, event):
        """Decorator for global functions as bound emitter function/methods.

        When the decorated method is binded to a bus, the functions's return value
        will be sent to the bus before being returned to the caller.

        A source can only emit one event. Multiple buses may be bounded to a source.
        When the source is called all binded buses will receive the event.

        Note:
            In use cases with multiple buses, the order that the buses receive the
            event is in order that they were binded. This is an implementation
            detail and is subject to change. Multi-thread usage is thus discouraged.

        Warning:
            Does not work on instance methods.
        """
        def decorator(func):
            emitter = self.makeEmitter(event, func)
            return emitter
        return decorator

    def addListener(self, event, func):
        """Add the provided function to the list of listeners of the provided event."""
        self._callbacks[event].append(func)
        _log.info('Add listener {} for event "{}"'.format(func, event))

    def makeEmitter(self, event, func):
        """Return an emitter function binded to the caller bus."""
        if isinstance(func, _Emitter):
            if not func.event == event:
                raise ExtraEmitError('An emitter may only emit one type of event.')
            func.buses.append(self)
            self._emitters[event].append(func)
            return func

        emitter = _Emitter(event, func)
        emitter.buses.append(self)
        self._emitters[event].append(emitter)

        _log.info('Created emitter {} for event "{}"'.format(func, event))
        return emitter


def on(event):
    """Unbound version of :meth:`Bus.on`.

    An unbounded callback must be binded to an event bus to be useful. Without
    a binding, the callback behaves just like a regular function.
    """
    if not isinstance(event, str):
        raise TypeError('Event string required.')

    def decorator(method):
        if hasattr(method, '_events'):
            method._events += event
        else:
            method._events = [event]
        return method
    return decorator


def source(event):
    """Unbound version of :meth:`Bus.source`.

    An unbounded source must be binded to an event bus to be useful. Without
    a binding, the emitter behaves just like a regular function.
    """
    if not isinstance(event, str):
        raise TypeError('Event string required.')

    def decorator(method):
        emitter = _Emitter(event, method)
        return emitter
    return decorator


class DeferedSource:
    def source(self, event):
        def wrapper(method):
            try:
                return self._bus.makeEmitter(event, method)
            except AttributeError:
                raise UnboundEmitter('Defered sources must be bound to an event bus.')
        return wrapper

import inspect
from functools import wraps

import pytest

import cryptle.event as event


class CallbackReached(Exception):
    pass


def reached(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        func(*args, **kwargs)
        raise CallbackReached
    return wrapper


def test_empty_emit():
    bus = event.Bus()
    with pytest.raises(event.NotListened):
        bus.emit('test_event', None)


def test_direct_emit():
    def callback(data):
        raise CallbackReached

    bus = event.Bus()
    bus.addListener('test_event', callback)
    with pytest.raises(CallbackReached):
        bus.emit('test_event', None)


def test_global_on():
    @event.on('test_event')
    def callback(data):
        assert data == None

    bus = event.Bus()
    bus.bind(callback)
    bus.emit('test_event', None)


def test_global_source_on():
    @event.source('test_event')
    def source():
        return None

    @event.on('test_event')
    def callback(data):
        assert data == None

    bus = event.Bus()
    bus.bind(source)
    bus.bind(callback)
    source()


def test_bound_bus_bound_callback():
    def callback(data):
        assert data == None

    evt = 'test_event'
    bus = event.Bus()
    bus.addListener(evt, callback)
    assert evt in bus._callbacks
    assert len(bus._callbacks[evt]) == 1


def test_Bus_source_to_function():
    bus = event.Bus()

    @reached
    @bus.source('test')
    def test():
        return 1

    with pytest.raises(event.NotListened):
        test()


def test_Bus_on_to_function():
    bus = event.Bus()

    @reached
    @bus.on('test')
    def test(data):
        pass

    bus.emit('test', None)


def test_unbound_on_method_unbound_bus():
    evt = 'test_event'

    class SMA:
        @event.on(evt)
        def test(self, data):
            assert data == None

    sma = SMA()
    bus = event.Bus()
    bus.bind(sma)
    assert evt in bus._callbacks
    assert len(bus._callbacks[evt]) == 1


def test_unbound_source_method_unbound_bus():
    evt = 'test_event'

    class Tick:
        @event.source(evt)
        def test(self):
            return 1

    tick = Tick()
    bus = event.Bus()
    bus.bind(tick)
    assert tick.test.buses[0] == bus
    assert tick.test.event

    with pytest.raises(event.NotListened):
        assert tick.test() == 1


def test_1_source_callback_combined_instance():
    class Ticker:
        @event.source('tick')
        def tick(self):
            return 1

        @reached
        @event.on('tick')
        def recv(self, data):
            assert data == 1

    ticker = Ticker()
    bus = event.Bus()
    bus.bind(ticker)
    with pytest.raises(CallbackReached):
        ticker.tick()


def test_1_source_instance_1_callback_instance():
    class Ticker:
        @event.source('tick')
        def tick(self, val=0):
            return val

    class Candle:
        @reached
        @event.on('tick')
        def recv(self, data, expect=0):
            assert data == expect

    ticker = Ticker()
    candle = Candle()

    bus = event.Bus()
    bus.bind(ticker)
    bus.bind(candle)

    with pytest.raises(CallbackReached):
        ticker.tick()


def test_1_callback_n_events():
    class Ticker:
        def __init__(self):
            self.called = 0

        @event.on('tick')
        def print_tick(self, data):
            self.called += 1
            return data

    bus = event.Bus()

    ticker = Ticker()
    bus.bind(ticker)
    bus.addListener('tick', ticker.print_tick)

    bus.emit('tick', 1)
    assert ticker.called == 2

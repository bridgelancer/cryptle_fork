import inspect
import pytest

import cryptle.event as event


class CallbackReached(Exception):
    pass


def test_empty_emit():
    bus = event.Bus()
    with pytest.raises(event.NotListenedWarning):
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


def test_bound_bus_bound_callback():
    def callback(data):
        assert data == None

    evt = 'test_event'
    bus = event.Bus()
    bus.addListener(evt, callback)
    assert evt in bus._callbacks
    assert len(bus._callbacks[evt]) == 1


def test_unbound_callback_method_unbound_bus():
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

    with pytest.raises(event.NotListenedWarning):
        assert tick.test() == 1


def test_1_source_and_callback_instance():
    class Ticker:
        @event.source('tick')
        def tick(self):
            return 1

        @event.on('tick')
        def recv(self, data):
            assert data == 1
            raise CallbackReached

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
        @event.on('tick')
        def recv(self, data, expect=0):
            assert data == expect
            raise CallbackReached

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

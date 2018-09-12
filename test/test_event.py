# Todo
import inspect
import cryptle.event as event
import pytest


def test_empty_emit():
    bus = event.Bus()
    with pytest.raises(event.NotListenedWarning):
        bus.emit('test_event', None)


def test_on():
    def callback(data):
        assert data == None

    evt = 'test_event'
    bus = event.Bus()
    bus.on(evt, callback)
    assert evt in bus._callbacks
    assert len(bus._callbacks[evt]) == 1


def test_on_and_emit():
    def callback(data):
        assert data == None

    bus = event.Bus()
    bus.on('test_event', callback)
    bus.emit('test_event', None)


def test_on_decorator():
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


def test_emit_decorator():
    evt = 'test_event'

    class Tick:
        @event.emit(evt)
        def test(self):
            return 1

    tick = Tick()
    bus = event.Bus()
    bus.bind(tick)
    assert len(tick.test._buses) == 1
    assert tick.test._buses[0] == bus
    assert tick.test._emits

    with pytest.raises(event.NotListenedWarning):
        assert tick.test() == 1


def test_class_pair():
    class Ticker:
        @event.emit('tick')
        def tick(self, val=0):
            return val

    class Candle:
        @event.on('tick')
        def recv(self, data, expect=0):
            assert data == expect

    ticker = Ticker()
    candle = Candle()

    bus = event.Bus()
    bus.bind(ticker)
    bus.bind(candle)

    ticker.tick()


def test_multiple_bind():
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
    bus.on('tick', ticker.print_tick)

    bus.emit('tick', 1)
    assert ticker.called == 2

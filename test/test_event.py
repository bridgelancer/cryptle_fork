# Todo
import inspect
import cryptle.event as event
import pytest


def test_empty_emit():
    loop = event.Loop()
    with pytest.raises(event.NotListenedWarning):
        loop.emit('test_event', None)


def test_on():
    def callback(data):
        assert data == None

    evt = 'test_event'
    loop = event.Loop()
    loop.on(evt, callback)
    assert evt in loop._callbacks
    assert len(loop._callbacks[evt]) == 1


def test_on_and_emit():
    def callback(data):
        assert data == None

    loop = event.Loop()
    loop.on('test_event', callback)
    loop.emit('test_event', None)


def test_on_decorator():
    evt = 'test_event'

    class SMA:
        @event.on(evt)
        def test(self, data):
            assert data == None

    sma = SMA()
    loop = event.Loop()
    loop.bind(sma)
    assert evt in loop._callbacks
    assert len(loop._callbacks[evt]) == 1


def test_emit_decorator():
    evt = 'test_event'

    class Tick:
        @event.emit(evt)
        def test(self):
            return 1

    tick = Tick()
    loop = event.Loop()
    loop.bind(tick)
    assert len(tick.test._loops) == 1
    assert tick.test._loops[0] == loop
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

    loop = event.Loop()
    loop.bind(ticker)
    loop.bind(candle)

    ticker.tick()


def test_multiple_bind():
    class Ticker:
        def __init__(self):
            self.called = 0

        @event.on('tick')
        def print_tick(self, data):
            self.called += 1
            return data

    loop = event.Loop()

    ticker = Ticker()
    loop.bind(ticker)
    loop.on('tick', ticker.print_tick)

    loop.emit('tick', 1)
    assert ticker.called == 2

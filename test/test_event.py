# Todo
import inspect
import cryptle.event as event
import pytest


def test_empty_emit():
    loop = event.Loop()
    with pytest.raises(Warning):
        loop.emit('test_event', None)


def test_internal_on():
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

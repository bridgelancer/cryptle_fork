# Todo

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


def test_listener_class():
    class SMA(event.Listener):
        def  __init__(self):
            event.Listener.__init__(self)

        @event.on('test_event')
        def test(self, data):
            assert data == None

    sma = SMA()
    loop = event.Loop()
    loop.bind(sma)
    loop.emit('test_event', data=None)

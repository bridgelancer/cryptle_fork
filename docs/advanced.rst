.. _advanced:

Advanced Usage
==============
This part of the documentation covers single, specific tasks in a step-by-step
instructions.

.. _datafeed_event:

Datafeed integration with event bus
-----------------------------------
:code:`cryptle.event.DeferedSource`
:meth:`cryptle.datafeed.Bitstamp.broadcast`


Event bus decorators
--------------------
The same function may be binded to multiple callbacks. This can be done through
either a bus instance, decorating a method multiple times, or by passing in
multiple event names to a decorator.

::

    def test(data):
        print(1)

    bus = Bus()
    bus.addListener('event', test)
    bus.emit('tick', data=1) // print 1 twice

::

    class Test:
        def __init__(self):
            self.called = 0

        @on('event')
        @on('event')
        def print_tick(self, _):
            self.called += 1

    test = Test()
    bus = Bus()
    bus.bind(test)
    bus.emit('event', data=None)

    assert test.called == 2  // True

::

    class Test:
        def __init__(self):
            self.data = 0

        @on('foo')
        @on('bar')
        def print_tick(self, data):
            self.data += data

    test = Test()
    bus = Bus()
    bus.bind(test)
    bus.emit('foo', data=1)
    assert test.data = 1  // True

    bus.emit('bar', data=2)
    assert test.data = 3  // True

DeferedSource

==================
Welcome to Cryptle
==================

Cryptle is a Python algorithmic trading framework. Get started with an overview
with :ref:`overview`. Those who are familiar with the framework can head over
:ref:`advanced` to find specific HOWTO recipes. For Cryptle in detail, the full
reference can be found in the :ref:`api` section.


.. _overview:

Overview
========
Creating a strategy with Cryptle::

   class FooStrat:
      # Todo

Event buses allow events to be generated and observed. An event always come with
a data object, though this object can be :code:`None`.

These data objects comes from return values of emitters. When emitter functions 
are called, an event with the return value as data is loaded into the event bus 
binded to the emitter function.

Lets see the event bus in action::

    import event

    class Ticker:
        @event.source('tick')
        def tick(self, val):
            return val

    class Candle:
        @event.on('tick')
        def recv(self, data):
            print(data) 

    ticker = Ticker()
    candle = Candle()

    bus = event.Bus()
    bus.bind(ticker)
    bus.bind(candle)

    ticker.tick(1)  // prints 1 to stdout

Methods decorated as callbacks can still be called normally::

    candle.recv(2)  // prints 2

and methods decorated as emitter will also return the value after it's emitted::

    assert 1 == ticker.tick(1)  // True

.. note::
   Event name can be any Python valid strings. However the recommended convention
   is 'subject:datatype'. (This is subject to change, a more powerful event
   parser is possibly coming soon.)

The event bus is a critical component of Cryptle. The event bus serves as the
middleware for communication/data-passing between trading engine components.
Unlike many well-established bus library, the Cryptle event bus processes events
synchronously. This guarantees that for any root event (an event that was not 
emitted by callbacks in the same bus), all subsequenct callbacks and events that
are triggered by the starting event will complete before the next emitted root 
event.

An asynchronous protocol could be implemented in the future.

.. note::
   The event bus does not make any effort in making a copy of event data for
   each callback. Hence if a piece of event data is modifible objects such as
   dictionary, callbacks that are called earlier could modify the value passed
   into later callbacks.


.. _advanced:

Advanced Usage
==============

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

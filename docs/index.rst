==================
Welcome to Cryptle
==================

Welcome to Cryptle's documentation. Cryptle is a Python algorithmic trading
framework. Get started with Cryptle at :ref:`overview`. Those who are familiar
with the framework can head over to :ref:`advanced` and find specific HOWTO
recipes. For Cryptle in detail, the full reference can be found in the
:doc:`api` section.


.. _overview:

Overview
========
Create and test a strategy with Cryptle::

    from cryptle.event import source, on
    from cryptle.datafeed import connect, BITSTAMP

    class Strat:
        @on('candle:btcusd')
        def handle(self, data):
            price = data['open']
            if price > 1000:
                self.buy()

        @source('buy')
        def buy(self, price):
            return price

    if __name__ == '__main__':
        # ...do stuff


Event Bus
---------
Event buses allow events to be generated and observed. An event always come with
a data object, though this object can be :code:`None`.

These data objects comes from return values of emitters. When emitter functions 
are called, an event with the return value as data is loaded into the event bus 
binded to the emitter function.

Lets see the event bus in action::

    from event import source, on, Bus

    @source('tick')
    def tick():
        return val
      
    class Candle:
        @on('tick')
        def recv(self, data):
            print(data) 

    candle = Candle()

    bus = Bus()
    bus.bind(tick)
    bus.bind(candle)

    tick(1)  // prints 1 to stdout

Functions or methods can be marked for binding with the decorators
:func:`source` and :func:`on`. :meth:`Bus.bind` registers marked functions and
marked methods of instance objects to an instance event bus.

Methods decorated as listeners can still be called normally::

    candle.recv(2)  // prints 2

and methods decorated as emitter will also return the value after it's emitted::

    assert 1 == tick(1)  // True

.. note::
   Event name can be any Python valid strings. However the recommended convention
   is 'subject:datatype'. (This is subject to change, a more powerful event
   parser is possibly coming soon.)

:meth:`Bus.source` and :meth:`Bus.on` are decorators serving the same purpose as
the module level decorators. These decorators associated with a bus instance
save the need for binding the decorated functions to a bus. They however can
only be used for module level functions::

    bus = Bus()

    @bus.source('event')
    def foo();
        return 1

    @bus.on('event')
    def bar(data):
        print data

    foo() // prints 1

.. todo explain this more clearly, go into how we cannot track instances created
   from class
.. note::
   The reason why this doesn't work on instance methods is due to the protocol
   with which class instance inherits instance methods from the class template.
   For example, :code:`A.f`, a method of class :code:`A`, is a actually global
   function, where as :code:`a.f`, where :code:`a = A()`, is a bound method.

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


Datafeed
--------


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

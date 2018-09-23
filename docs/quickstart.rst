.. _quickstart:

Quickstart
==========
This page gives a basic introduction to Cryptle.

Overview
--------
Create and test a strategy with Cryptle::

    from cryptle.event import source, on, Bus
    from cryptle.datafeed import Bitstamp as Feed
    from cryptle.exchange import Bitstamp as Exchange

    class Strat:
        @on('trades:btcusd')
        def handle(self, data):
            price = data['price']
            if price > 1000:
                self.buy()

        @source('buy:btcusd')
        def buy(self, price):
            return price

    if __name__  == "__main__":
        bus      = Bus()
        feed     = Feed()
        strat    = Strat()
        exchange = Exchange()

        bus.bind(feed)
        bus.bind(strat)
        bus.bind(exchange)

        feed.connect()
        feed.broadcast('trades:btcusd')


Datafeed
--------
Supported datafeeds include Bitstamp and Bitfinex. Datafeed classes generally
has the following interfaces:

:code:`connect()` starts a thread for a long-polled socket that sends and
receives messages.

:code:`disconnect()` stops the socket and thread.

:code:`connected` is a boolean for whether the socket is still connected to the
data source server.

:code:`on()` registers callback for provided events. Generally the most used
function.


Exchange
--------
Todo.


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


Datafeed integration with event bus
-----------------------------------
:code:`cryptle.event.DeferedSource`
:meth:`cryptle.datafeed.Bitstamp.broadcast`

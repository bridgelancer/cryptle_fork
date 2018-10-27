.. _guides:

User guides
===========
This part of the documentation breaks down each Cryptle subsystems one by one.


Datafeed
--------
In Cryptle, datefeed is a package of drivers to streamed data with a unified set
of methods. The intention is to provide a consistent interface for both internal
and external data sources. A connection can be established using
:func:`~cryptle.datafeed.connect`::

   import cryptle.datafeed as datafeed

   def print_ticks(tick):
       print(tick)

   feed = datafeed.connect(datafeed.BITSTAMP)
   feed.on('tick', print_ticks)

The example above used the :meth:`~cryptle.datafeed.Datafeed.on` method to setup
callback for events from the datafeed object.

Each datafeed driver has their own set of available events, more often than not
named differently by it's respecitve sources, even when they're the same type of
data. When this is the case, the driver module will provide helpers
``decode_event`` and ``encode_event`` for conversion between the Cryptle
standardised event names and the third party names. For datafeed users this
should not be a concern as it should be hidden under the abstraction layer.

The full list of standard datafeed events can be found at `todo`.

Datafeed object can also be used as context managers that disconnects gracefully
upon error::

   with connect(datafeed.BITSTAMP) as feed:
       # feed.on(...)

These are the datafeeds that come with the default Cryptle distribution:

- Bitstamp
- Bitfinex

.. seealso::
   Some datafeeds have specialized :ref:`integration <datafeed_event>` with the
   event bus.


Exchange
--------
Exchanges are interfaces for placing orders to buy and sell assets. Some
exchange interfaces includes account functionality. All supported exchanges at
present use REST APIs, so no persistent connection is required. Nonetheless,
the exchange creation function is named
:meth:`~cryptle.exchange.Exchange.connect`, in case for forward compatibility.

Creation of exchange objects follow a similar interface as the datafeed package.

Example code::

    from cryptle.exchange import connect, BITSTAMP

    exchange = connect(BITSTAMP)
    exchange.marketBuy('bchusd', 100.0)

Functino call for limit orders return an order ID for tracking the order. The
recommended method for using limit orders is with the event bus. This way the
order tracking boilerplate code can be delegated to the framework.


Backtesting and Paper Trading
-----------------------------
The module :mod:`backtest` and class :class:`Paper` is the heart and soul of
backtesting in Cryptle.


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


.. _events:

Standard Events
---------------
Todo.


.. _registry_ref:

Registry
--------
Registry handles :class:`Strategy` class's state information and controls the order
and timing of logical tests' execution. The logical tests to be ran should be
submitted in a Dictionary to the **setup** argument with an 'actionname' as a key
followed by timing,constraints and order contained in a list. The following is
an example::

   setup = {'doneInit': [['open'], [['once per bar'], {}], 1],
            'wma':      [['open'], [['once per bar'], {'n per signal': ['doneInit', 10]}], 2]}

In the above scenario, the :class:`Registry` class will be dynamically listening
for tick. Once the timing of execution is met and the constraints fulfiled, a
:class:`registry:execute` signal will be emitted. The planned action :meth:`doneInit`
will be triggered upon receiving the signal. :class:`Registry` will then
look at the timing of execution and contraints chosen for the next action.
We see that the second item
:meth:`wma`  in `setup` differs to the former in one extra constraint which
translates to only performing the action 10 times in maxima per signal upon
the completion of `doneInit`.

Currently the following actions and constraints are supported.

Actions:
   - ``open``
   - ``close``

Constraints:
   - ``once per bar``
   - ``once per trade``
   - ``once per period``
   - ``once per signal``
   - ``n per bar``
   - ``n per period``
   - ``n per trade``
   - ``n per signal``


.. _timeseries_ref:

Timeseries
----------
Timeseries is a stand alone class that handles a list-based data input and
compute the value. Currently, the class only supports bar-by-bar update. For
any Timeseries, a `self._ts` needs to be implemented during construction. The instance
listens to any update in value of `self._ts`. Each realization of :class:`Timeseries`
implements a :meth:`evaluate` which runs on every update.

An option of adding a decorator :meth:`Timeseries.cache` to :meth:`evaluate` has
been provided. This creates a `self._cache`, which could be referenced to within
the `evaluate` function for past values of the listened Timeseries. The number
of items stored is regulated by `lookback`.

For any subseries held within a wrapper class intended to be accessed by the
client, a :class:`GenericTS` could be implemented. The format of the function
signature is as following: someGenericTS(ts to be listened, lookback, eval_func,
args). The :meth:`eval_func` should be implemented in the wrapper class and the `args` are
the arguments that are passed into the :meth:`eval_func`.




.. _guides:

Topic guides
============
This part of the documentation breaks down each Cryptle subsystems one by one.


Datafeed
--------
In Cryptle, datefeed is a package of drivers to streamed data with a unified set
of methods. The intention is to provide a consistent interface for both internal
and external data sources. A connection can be established using
:func:`~cryptle.datafeed.connect`:

.. code:: python

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

The full list of standard datafeed events can be found at ``todo``.

Datafeed object can also be used as context managers that disconnects gracefully
upon error:

.. code:: python

   with connect(datafeed.BITSTAMP) as feed:
       # feed.on(...)

These are the datafeeds that come with the default Cryptle distribution:

- Bitstamp
- Bitfinex


Exchange
--------
Exchanges are interfaces for placing orders to buy and sell assets. Some
exchange interfaces includes account functionality. All supported exchanges at
present use REST APIs, so no persistent connection is required. Nonetheless,
the exchange creation function is named
:meth:`~cryptle.exchange.connect`, in case for forward compatibility.

Creation of exchange objects follow a similar interface as the datafeed package.

Example code:

.. code:: python

    from cryptle.exchange import connect, BITSTAMP

    exchange = connect(BITSTAMP)
    exchange.marketBuy('bchusd', 100.0)

Functino call for limit orders return an order ID for tracking the order. The
recommended method for using limit orders is with the event bus. This way the
order tracking boilerplate code can be delegated to the framework.


.. _strategy:

Strategy
--------
In Cryptle, all concrete implementations of strategies must inherit from the
base :class:`~cryptle.strategy.Strategy` class, or generic strategy classes that
are children of Straegy. These generic strategies provide take common idioms and
patterns in stratgy development and abstract them. The Strategy base class
provides basic features that manages ownership of a
:class:`~cryptle.strategy.Portfolio` object and relationship to a
:class:`~cryptle.datafeed.Datafeed`.

Events from the market are handle by callbacks for each corresponding data type.
For instance, to recieve live market trade data, implement the ``onTrade()``
method. The input data can be provided through by the corresponding
``pushTrade()``. The full list of supported data input interface can be found
in the :class:`~cryptle.strategy.Strategy` reference.

Here's a very basic strategy where we will buy whenever the price of the
particular asset:

.. code:: python

   class FooStrategy(SingleAssetStrategy):
       def __init__(self, asset, target):
           SingleAssetStrategy.__init__(self, asset)
           self.price_target = target

       def onTrade(self, price, timestamp, amount, action):
           if price > self.price_target:
               self.buy(amount)

   exchange = cryptle.exchange.connect(BITSTAMP)

   strat = FooStrategy('bch', 100)
   strat.exchange = exchange

   # Setup and start a datafeed. Stream into the strategy using the pushTrade()
   # or pushCandle() methods.


The event bus mechanicism is very useful for placing and keeping tracking of
limit orders. The mixin class :class:`~cryptle.strategy.OrderEventMixin`
overrides the normal buy/sell methods into marked instance methods that emit
events into a :class:`~cryptle.event.Bus`. The mixin must come before the base
strategy class. Detailed reference of the mixin events are at
:class:`~cryptle.strategy.EventOrderMixin`.

The code looks mostly the same:

.. code:: python

   class BusStrategy(EventOrderMixin, Strategy):
       def onTrade(self, price, t, amount, action):
           if price > self.price_target:
               self.marketbuy(amount)

   strat = BusStrategy()
   exchange = cryptle.exchange.connect(BITSTAMP)

   bus = Bus()
   bus.bind(strat)
   bus.bind(exchange)

Other mixins are covered in the :mod:`strategy <cryptle.strategy>` module
reference documentation.

.. seealso::

   For questions about what is a mixin and why are they useful, StackOverflow
   has an excellent `explanation
   <https://stackoverflow.com/questions/533631/what-is-a-mixin-and-why-are-they-useful>`_.
   Furthermore, Django is a great framework to for more `examples
   <https://docs.djangoproject.com/en/2.0/topics/class-based-views/mixins/>`_
   of mixins.


Event Bus
---------
Event buses allow events to be generated and observed. An event always come with
a data object, though this object can be ``None``.

These data objects comes from return values of emitters. When emitter functions
are called, an event with the return value as data is loaded into the event bus
binded to the emitter function.

Lets see the event bus in action:

.. code:: python

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

Let break this down line by line.

1. First we imported three things. The class :class:`~cryptle.event.Bus` is core
   to the :mod:`~cryptle.event` module and serves as a message broker.  The
   :func:`~cryptle.event.source` and :func:`~cryptle.event.on`, are
   decorators for marking functions and methods and to be binded to an event
   bus.

2. Next we marked the function ``tick`` as a *source* for the event ``tick``.

Methods decorated as listeners can still be called normally:

.. code:: python

    candle.recv(2)  // prints 2

and methods decorated as emitter will also return the value after it's emitted:

.. code:: python

    assert 1 == tick(1)  // True

.. note::

   Event name can be any Python valid strings. However the recommended convention
   is 'subject:datatype'. (This is subject to change, a more powerful event
   parser is possibly coming soon.)

:meth:`~cryptle.event.Bus.source` and :meth:`~cryptle.event.Bus.on` are
decorator methods serving the same purpose as the module level decorators. These
decorators associated with a bus instance save the need for binding the
decorated functions to a bus. They however can only be used for module level
functions and not instance methods:

.. code:: python

    bus = Bus()

    @bus.source('event')
    def foo();
        return 1

    @bus.on('event')
    def bar(data):
        print data

    foo() // prints 1

.. note::

   The reason why this doesn't work on instance methods is due to the python
   object protocol with method resolution. Python objects get their instance
   methods from binding itself to the methods from the class template.

   For example, ``A.f``, a method in class ``A``, is a actually global
   function, where as ``a.f``, where ``a = A()``, is a bound method.

   Since the Cryptle event bus works by tagging meta information onto marked
   functions and methods, these information are lost when a bound method is
   created from the function template in the class object. While a work around
   exists by using metaclasses, it interfers too much with the user code and it
   is therefore opted to leave this feature out of the framework.

The event bus is a critical component of Cryptle. The event bus serves as the
middleware for communication between trading engine components.

Unlike many well-established message library, the Cryptle event bus processes
events synchronously. This guarantees that for any root event (an event that was
not emitted by callbacks in the same bus), all subsequenct callbacks and events
that are triggered by the starting event will complete before the next emitted
root event.

.. note::

   The event bus does not make any effort in making a copy of event data for
   each callback. Hence if a piece of event data is modifible objects such as
   dictionary, callbacks that are called earlier could modify the value passed
   into later callbacks.

Up until now all the emitted events by either functions or methods must be
marked at the time of their declaration. This restricts the ability of objects
to dynamically emit events into a bus. A solution to this is the base class
:class:`~cryptle.event.DeferedSource`.

:class:`~cryptle.event.DeferedSource` is a mixin class with a decorator method
:meth:`~cryptle.event.DeferedSource.source` that allows objects to create an
event emitting function in instance methods and emit arbitrary events.

Here is an example from the datefeed module:

.. code:: python

   class Bitstamp(BitstampFeed, DeferedSource):
       """Simple wrapper around BitstampFeed to emit data into a bus."""
       def broadcast(self, event):
           @self.source(event)
           def dummy_func(data):
               return data
           self.on(event, dummy_func)

   feed = Bitstamp()
   feed.broadcast('tick')  # only tick data will be emitted into the event bus

The following are some more complex examples of using the event bus, such as
binding a function to listen for multiple events.

.. code:: python

    def test(data):
        print(1)

    bus = Bus()
    bus.addListener('event', test)
    bus.emit('tick', data=1) // print 1 twice

.. code:: python

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

.. code:: python

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


.. _events:

Standard Events
---------------
- ``trades(price, timestamp, volume, type)`` new trade market event
- ``candles(open, high, low, close, volume, timestamp)`` new candlesticks
- Time related: :class:`~cryptle.clock.Clock`


.. _registry_ref:

Registry
--------
Registry handles :class:`Strategy` class's state information and controls the order
and timing of logical tests' execution. The logical tests to be ran should be
submitted in a Dictionary to the **setup** argument with an 'actionname' as a key
followed by timing,constraints and order contained in a list. The following is
an example:

.. code:: python

   setup = {'doneInit': [['open'], [['once per bar'], {}], 1],
            'wma':      [['open'], [['once per bar'], {'n per signal': ['doneInit', 10]}], 2]}

In the above scenario, the :class:`Registry` class will be dynamically listening
for tick. Once the timing of execution is met and the constraints fulfiled, a
``registry:execute`` signal will be emitted. The planned action :meth:`doneInit`
will be triggered upon receiving the signal. :class:`Registry` will then
look at the timing of execution and contraints chosen for the next action.
We see that the second item
:meth:`wma`  in ``setup`` differs to the former in one extra constraint which
translates to only performing the action 10 times in maxima per signal upon
the completion of ``doneInit``.

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
Finanical data can often be organised into time series. This goes for both raw
data (e.g. price ticker) and processed data (e.g. moving average).
:class:`~metric.base.Timeseries` class is a data container for handling such data, especailly
when the data is being streamed in real-time.

.. warning::

   This section only documents :class:`~metric.base.Timeseries`, the class
   responsible for computation and dependencies of a time series. The new
   components in the time series hierarchy: :class:`~metric.base.TimeseriesWrapper`,
   and :class:`~metric.base.HistoricalTS` were left out. Full documentation is
   under way.

To allow time series data to be collected and computed in real-time, the
`observer pattern <https://en.wikipedia.org/wiki/Observer_pattern>`_ is
integrated into the class's interface.

The timeseries base class is designed to be both an observable and an observer.
This means that each instance of a Timeseries class has corresponding
`publish-subscribe <https://en.wikipedia.org/wiki/Publish%E2%80%93subscribe_pattern>`_
methods that lets it broadcast changes to other objects that are listening to
its updates, while also listening for updates from other timeseries.

To make all this work, subclasses of :class:`Timeseries` must do the following:

1. Call the base :meth:`Timeseries.__init__`, passing the upstream Timeseries
   object as argument.
2. Implement :meth:`~metric.base.Timeseries.evaluate` which gets called on
   updates of what they.
3. Declare an attribute ``_ts`` (ts shortform for timeseries) in the
   constructor. The instance will listen for any update in ``self._ts``.

.. note::

   Some Timseries object (e.g. CandleStick) has no observable to keep track of.
   Rather, they act as a source of data for other types of Timeseries objects to
   listen to. Hence, for CandleStick (or other source Timeseries), their data
   source should be constructed by an Event via the Event bus architecture.

Another feature Timeseries is the decorator :meth:`~metric.base.Timeseries.cache`.
This decorator can be used on :meth:`~metric.base.Timeseries.evaluate` to
provide a local copy of historical values of the upstream Timeseries, stored in
``self._cache``. The number of items stored is restricted by
``self._lookback``.

An example of Timeseries might look like:

.. code:: python

   class Foo(Timeseries):
       def __init__(self, ts, lookback):
           super().__init__(ts=ts)
           self._lookback = lookback
           self._ts = ts

       # generate self._cache for accessing historical self._ts value
       @Timeseries.cache
       def evaluate(self):
           # some code that would be updated when ts updates

If a Timeseries is designed to listen to multiple Timeseries objects
for updates, the only supported behaviour of updating is to wait till all the
listened timeseries to update at least once before its :meth:`evaluate` function
to run. In this case, the ``self._ts`` attribute should be set to a list of the
Timeseries objects to be listened to:

.. code:: python

   class FooMultiListen(Timeseries):
       def __init__(self, ts1, ts2, lookback):
           self._ts       = [ts1, ts2]
           self._lookback = lookback
           super().__init__(ts=self._ts)

For any subseries held within a wrapper class intended to be accessed by the
client, a :class:`~metric.base.GenericTS` could be declared within the
construction of the wrapper class. The format of the
:meth:`~metric.base.GenericTS.__init__` follows:
``someGenericTS(timeseries_to_be_listened, lookback, eval_func, args)``. The
:meth:`eval_func` should be implemented in the wrapper class and the ``args`` are
the arguments that are passed into the :meth:`eval_func`:

.. code:: python

   class foo_with_GenereicTS(Timeseries):
       def __init__(self, ts, lookback):
           super().__init__(ts=ts)
           self._lookback = lookback
           self._ts = ts

       def eval_foo1(*args):
           # act as normal evaluate function in Timeseries, to be passed into Generic TS

       def eval_foo2(*args, **kwargs):
           # same as above

       # foo1 is the subseries that is held by foo_with_GenereicTS
       self.foo1 = GenericTS(ts, lookback=lookback, eval_func=eval_foo1, args=[self])
       self.foo2 = GenericTS(ts, lookback=lookback, eval_func=eval_foo2, args=[self])

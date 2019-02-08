.. _guides:

Topic guides
============
This part of the documentation breaks down each Cryptle subsystems one by one.


Datafeed
--------
In Cryptle, datefeed is a package of drivers to streamed data with a unified set of
methods. The intention is to provide a consistent interface for both internal and
external data sources. A connection can be established using
:func:`~cryptle.datafeed.connect`:

.. code:: python

   import cryptle.datafeed as datafeed

   def print_ticks(tick):
       print(tick)

   feed = datafeed.connect(datafeed.BITSTAMP)
   feed.on('tick', print_ticks)

The example above used the :meth:`~cryptle.datafeed.Datafeed.on` method to setup
callback for events from the datafeed object.

Each datafeed driver has their own set of available events. More often than not similar
types of data would be named differently by their respecitve sources.

.. note::

   When this is the case, the driver module will provide helpers ``decode_event`` and
   ``encode_event`` for conversion between the Cryptle standardised event names and the
   third party names. For datafeed users this should not be a concern as it should be
   hidden under the abstraction layer.

   \*\*deprecated since 0.14\*\*

The full list of standard datafeed events can be found at ``todo``.

These are the datafeeds that come with the default Cryptle distribution:

- Bitstamp
- Bitfinex


Exchange
--------
Exchanges are interfaces for placing orders to buy and sell assets. Some exchange
interfaces includes account functionality.

Creation of exchange objects follow a similar interface as the datafeed package.

Example code:

.. code:: python

    from cryptle.exchange import connect, BITSTAMP

    exchange = connect(BITSTAMP)
    exchange.marketBuy('bchusd', 100.0)

Function call for limit orders return an order ID for tracking the order. The
recommended method for using limit orders is with the event bus. This way the order
tracking boilerplate code can be delegated to the framework.

The standard exchange API is documented in the reference document at
:class:`cryptle.exchange.Exchange`.

.. _strategy:

Strategy
--------
In Cryptle, all concrete implementations of strategies must inherit from the base
:class:`~cryptle.strategy.Strategy` class, or generic strategy classes that are children
of Straegy. These generic strategies provide take common idioms and patterns in stratgy
development and abstract them. The Strategy base class provides basic features that
manages ownership of a :class:`~cryptle.strategy.Portfolio` object and relationship to a
:class:`~cryptle.datafeed.Datafeed`.

Events from the market are handle by callbacks for each corresponding data type.  For
instance, to recieve live market trade data, implement the ``onTrade()`` method. During
runtime, the strategy can be manually triggered by calling the method ``pushTrade()``
with the approperiate market data as input arguments. The full list of supported data
input interface can be found in the :class:`~cryptle.strategy.Strategy` reference.

Here's a very basic strategy where we will buy whenever the price of the particular
asset:

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


The :ref:`event_bus` mechanicism is very useful for placing and keeping tracking of
limit orders. The mixin class :class:`~cryptle.strategy.OrderEventMixin` overrides the
normal buy/sell methods into marked instance methods that emit events into a
:class:`~cryptle.event.Bus`. The mixin must come before the base strategy class.
Detailed reference of the mixin events are at
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

Other mixins are covered in the :mod:`strategy <cryptle.strategy>` module reference
documentation.

.. seealso::

   For questions about what is a mixin and why are they useful, StackOverflow has an
   excellent `explanation
   <https://stackoverflow.com/questions/533631/what-is-a-mixin-and-why-are-they-useful>`_.
   Furthermore, Django is a great framework to for more `examples
   <https://docs.djangoproject.com/en/2.0/topics/class-based-views/mixins/>`_ of mixins.


.. _event_bus:

Event Bus
---------
Event buses allow events to be generated and observed. An event always come with a data
object, though this object can be ``None``.

These data objects comes from return values of emitters. When emitter functions are
called, an event with the return value as data is loaded into the event bus binded to
the emitter function.

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

1. First we imported three things. The class :class:`~cryptle.event.Bus` is core to the
   :mod:`~cryptle.event` module and serves as a message broker.  The
   :func:`~cryptle.event.source` and :func:`~cryptle.event.on`, are decorators for
   marking functions and methods and to be binded to an event bus.

2. Next we marked the function ``tick`` as a *source* for the event ``tick``.

Methods decorated as listeners can still be called normally:

.. code:: python

    candle.recv(2)  // prints 2

and methods decorated as emitter will also return the value after it's emitted:

.. code:: python

    assert 1 == tick(1)  // True

.. note::

   Event name can be any Python valid strings. However the recommended convention is
   'subject:datatype'. (This is subject to change, a more powerful event parser is
   possibly coming soon.)

:meth:`~cryptle.event.Bus.source` and :meth:`~cryptle.event.Bus.on` are decorator
methods serving the same purpose as the module level decorators. These decorators
associated with a bus instance save the need for binding the decorated functions to a
bus. They however can only be used for module level functions and not instance methods:

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

   The reason why this doesn't work on instance methods is due to the python object
   protocol with method resolution. Python objects get their instance methods from
   binding itself to the methods from the class template.

   For example, ``A.f``, a method in class ``A``, is a actually global function, where
   as ``a.f``, where ``a = A()``, is a bound method.

   Since the Cryptle event bus works by tagging meta information onto marked functions
   and methods, these information are lost when a bound method is created from the
   function template in the class object. While a work around exists by using
   metaclasses, it interfers too much with the user code and it is therefore opted to
   leave this feature out of the framework.

The event bus is a critical component of Cryptle. The event bus serves as the middleware
for communication between trading engine components.

Unlike many well-established message library, the Cryptle event bus processes events
synchronously. This guarantees that for any root event (an event that was not emitted by
callbacks in the same bus), all subsequenct callbacks and events that are triggered by
the starting event will complete before the next emitted root event.

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

Built-in Events
---------------
- ``trades(price, timestamp, volume, type)`` new trade market event
- ``candles(open, high, low, close, volume, timestamp)`` new candlesticks
- Time related: :class:`~cryptle.clock.Clock`


.. _scheduler_ref:

Scheduler
--------
It is often a nightmare to manage flags and restraining the execution of
Strategy methods while implementing a trading strategy.
:class:`~cryptle.scheduler.Scheduler`, together with
:class:`~cryptle.codeblock.CodeBlock` and
:class:`~cryptle.codeblock.LogicStatus`, is a set of integral solution of
mitigating the inadverent uses of class flags and promoting source code
maintainability of Strategy class.

:class:`~cryptle.scheduler.Scheduler` handles :class:`~cryptle.strategy.Strategy`
class's state information and controls the order and restraints of function
blocks execution.

.. warning::

   Scheduler might change to another name to better reflect its
   true functionality within the Strategy/CodeBlocks framework.

The methods of a Strategy class requiring control should be passed in a ``list``
of ``tuple`` to the ``setup`` argument of the constructor of the Scheduler. The
order of execution of the Strategy methods to be controlled by the Scheduler
would check and execute as in its tuple entry in the order of the list.

There is a predefined structure for the tuple to wrap a Strategy method. Within
the tuple there are sub-tuples that specify the timing of exection (whenExec)
and constraints that limit the execution of these Strategy methods. The first
sub-tuple would be be ('codeblock', function_pointer) and the second tuple would
be ('whenExec', time_of_execution). The third tuples onwards are the constraints
and flags. They take the format of ('constraint_name', {keys: args})

The dictionary specified within the tuple of constraints and flags consists of
predefined string keys to convey information of that particular constraint to the
Scheduler. The available keys and their use are:

key:
   -  ``type``: the type of constraint category this constrinat belongs to
   -  ``event``: the type of Event that refresh this constraint
   -  ``refresh_period``: the number of events needed to refresh this constraint
   -  ``max_trigger``: the number of allowable triggers for the Strategy
     function before refreshing
   -  ``funcpt`` (optional): the reference of Strategy function that refers to
     the CodeBlock containing the required flag, only for once per flag/n per
     flag type.


During construction of the Scheduler, :class:`~cryptle.scheduler.Scheduler` would
create an attribute ``codeblocks``. This holds a list of
:class:`~cryptle.codeblock.CodeBlock` objects.
:class:`~cryptle.codeblock.CodeBlock` would be documented separately in this
guide but the essence is that it provides interface for
:class:`~cryptle.scheduler.Scheduler` to properly maintain the actual
``logic_status`` of the Strategy methods.

.. code:: python

   class Scheduler:
      def __init__(self, *setup):
         self.codeblocks = list(map(CodeBlock, *setup))

.. note::

   This is not complying to the design intent of the rest of the framework. In
   the future the Scheduler should not directly handle data source. Instead the
   data handling part should be delegated to the Strategy instance with the use
   of the :class:`~cryptle.strategy.Strategy` interfaces provided.

The control of the execution of the methods of the Strategy was achieved by the
combined use of various **onEvent** functions such as
:meth:`~cryptle.scheduler.Scheduler.onTick`,
:meth:`~cryptle.scheduler.Scheduler.refreshLogicStatus` and the
:meth:`~cryptle.scheduler.Scheduler.check` method.  **onEvent** functions could
listen to an external source via the Event bus architecture in order to update
its internal state for the Strategy, or being directly called by the Strategy.

.. code:: python

   class Scheduler:
      def __init__(self, *setup):
         # other appropriate initialization
         self.codeblocks = list(map(CodeBlock, *setup))

      @on('tick') # decorated to allow invocation by Event bus
      def onTick(self, tick):
         # Implmentation to update local state
         self.handleCheck(tick)

      @on('new_candle') # decorated to allow invocation by Event bus
      def onCandle(self, bar):
         self.refreshLogicStatus(codeblock, 'candle')


   class FooStrat(Strategy):
      def __init__(self):
         # appropriate initialization of setup and other components
         self.scheduler = Scheduler(setup)

      def onTrade(self, price, timestamp, amount, action):
         # receive data and kickstart all relevant Bus-related Events
         self.scheduler.onTick(tick)

The Strategy :meth:`~cryptle.Strategy.onTrade` method calls Scheduler to cascade
the new information and triggers the necessary updating and checking.

.. code:: python

   class Scheduler:
      # ...

      @on('tick')
      def onTick(self, tick):
         # Implmentation to update local state
         self.handleCheck(tick)

      def refreshLogicStatus(self):
         # Implmentation to update CodeBlock LogicStatus

      def handleCheck(self, tick)
         self.check(codeblock)

      def check(self, codeblock):
         # Implementation to check executability of individual CodeBlocks
         if someCondition:
            # execute this codeblock if fullfilled someCondition
            codeblock.check()

Schematic representation of how Scheduler cascade the information to check
executability of individual CodeBlock held in ``codeblocks``.

In the above scenario, the :class:`Scheduler` class will listen for tick via
:meth:`~cryptle.scheduler.Scheduler.onTick`. Upon each arrival of tick, the
:meth:`~cryptle.scheduler.Scheduler.check` function would be called. If all the
conditions to execute a particular Strategy method are fulfilled, the indiviudal
:class:`~cryptle.codeblock.CodeBlock` of the :class:`~cryptle.scheduler.Scheduler`
would be called and updated to execute the function and update the local
:class:`~cryptle.codeblock.CodeBlock` ``logic_status``, ``flags`` and
``localdata``  for the Strategy method.

.. code:: python

   class Scheduler:
      # ...

      def check(self, codeblock):
         # Implementation to check executability of individual codeblock
         if someCondition:
            # execute this codeblock if fullfilled someCondition
            codeblock.check(num_bars, info)

   class CodeBlock:
      def __init__(self, *entry):
         self.logic_status = LogicStatus(whenExec, constraints_and_flags)
         self.triggered = False
         self.flags = {}
         self.localdata = {}

      def check(self, num_bars, flagvalues):
         # Implementation to execute the Strategy function and update the #
         # localdata/flags
         flagValues, flagCB = unpackDict(*flagvalues)
         self.triggered, self.flags, self.localdata = self.func(flagValues, flagCB, **self.localdata)

         # Also updates LogicStatus subsequently

These ``logic_status`` are also dependent on :class:`~class.scheduler.Scheduler` for
its proper maintenance under relevant changes of the external state. In this case,
the :meth:`~cryptle.scheduler.Scheduler.refreshLogicStatus` is responsible for
refreshing the LogicStatus appropriately.

.. _codeblocks_ref:

CodeBlock
---------
CodeBlock is both a data structure containing meta-information and also an
abstraction layer for maintaing these meta-information of a Strategy method.

It provides necessary interface for both :class:`~cryptle.scheduler.Scheduler` and
Strategy methods to systematically access and update the values of ``logic_status``
and maintain the values of ``flags`` and ``localdata``.

``logic_status`` of the :class:`~cryptle.codeblock.Codeblock` is a separate object
that has its own segregated mechanism of maintaining the its representation of
``logic_status`` as a ``Dictionary``.

``flags`` are data maintained by one particular
:class:`~cryptle.codeblock.Codeblock` that are intended to be accessed by the
other :class:`~cryptle.codeblock.Codeblock`.

``localdata`` are data local to that particular
:class:`~cryptle.codeblock.Codeblock` and not intented to be accessed by other
:class:`~cryptle.codeblock.Codeblock`.

Several class methods are available for :class:`~cryptle.scheduler.Scheduler` to
call during various situations. The ``logic_status`` of inidivdual
:class:`~cryptle.codeblock.CodeBlock` are initialized by
:meth:`~cryptle.codeblock.CodeBlock.initialize` when the setup ``sub-tuples``
was first passed into the constructor of the Scheduler.

:class:`~cryptle.scheduler.Scheduler` then checks conditions based on the
individual :class:`~cryptle.codeblock.LogicStatus` of a
:class:`~cryptle.codeblock.CodeBlock`. During execution of a Strategy method,
any updates of the own ``localdata``, ``flags`` would be returned by the
Strategy method itself. Any update of **other** CB's ``localdata`` should
pass an ``Dictionary`` of format {'flagname': value}  within the method to call
the other CB's :meth:`~cryptle.codeblock.CodeBlock.setLocalData` method.

The following is a complete example:

.. code:: python

   class FooStrat(Strategy):
      # appropriate initialization including setup ..
      self.setup = [
               (
                  ('codeblock', foo),
                  ('whenExec', 'open'),
                  ('once per bar', {'type': 'once per bar', 'event': 'bar', 'refresh_period': 1}),
               ),

               (
                  ('codeblock', bar),
                  ('whenExec', 'close'),
                  ('once per bar', {'type': 'once per bar', 'event': 'bar', 'refresh_period': 1}),
                  (
                     'fooflag',
                     {
                        'type': 'n per flag',
                        'event': 'flag',
                        'refresh_period': 1,
                        'max_trigger': 10000000,
                        'funcpt': foo
                     }
                  ),
               ),
            ]

      def foo(flagValues, flagCB, fooflag=None, dummy=True):
         # to be stored both as a localdatum and flag
         dummy = True

         if fooflag is None:
            # to be stored both as a localdatum and flag
            fooflag = True

         if not fooflag:
            fooflag = True
         if fooflag:
            fooflag = False

         if dummy:
            print('dummy is True')
         else:
            print('dummy is False')

         triggered = True
         localdata = {'fooflag': fooflag, 'dummy': dummy}
         flags = {'fooflag': fooflag, 'dummy': dummy}
         # must return these three for updating CodeBlock`
         return triggered, flags, localdata

      def bar(flagValues, flagCB, localdata=None):
         # syntax for accessing other CB's flag
         fooflag = flagValues['fooflag']
         if fooflag:
            print('foo flag is true')
            # syntax for modifying other CB's flag
            flagCB['dummy'].setLocalData({'dummy': True})
         else:
            print('foo flag is false')
            flagCB['dummy'].setLocalData({'dummy': False})

         triggered = True
         localdata = {}
         flags = {}
         # must return these three for updating CodeBlock`
         return triggered, flags, localdata

If the codes in the Strategy method determines that this prompts a successful
triggering to update the ``logic_status``, the client function should return
True for ``triggered`` and the ``logic_status`` would be correspondingly updated
by :meth:`~cryptle.codeblock.CodeBlock.update`.

The :meth:`~cryptle.codeblock.Codeblock.refresh` method would be called by the
:meth:`~cryptle.scheduler.Scheduler.refreshLogicStatus` method of the
:class:`~cryptle.scheduler.Scheduler`. For details, please refer to the
documentation of the Scheduler.

.. _timeseries_ref:

Timeseries
----------
Finanical data can often be organised into time series. This goes for both raw
data (e.g. price ticker) and processed data (e.g. moving average).
:class:`~cryptle.metric.base.Timeseries` class is a data container for handling
such data, especailly when the data is being streamed in real-time.

To allow time series data to be collected and computed in real-time, the
`observer pattern <https://en.wikipedia.org/wiki/Observer_pattern>`_ is
integrated into the class's interface.

The Timeseries base class is designed to be both an observable and an observer.
This means that each instance of a Timeseries class has corresponding
`publish-subscribe
<https://en.wikipedia.org/wiki/Publish%E2%80%93subscribe_pattern>`_ methods that
let it broadcast changes to other objects that are listening to its updates,
while also listening for updates from other timeseries.

To make all these work, subclasses of :class:`Timeseries` must do the following:

1. Call the base :meth:`Timeseries.__init__`, passing the upstream Timeseries
   object as argument.
2. Implement :meth:`~cryptle.metric.base.Timeseries.evaluate` which gets called
   on updates of what they listen to.
3. Declare an attribute ``_ts`` (ts shortform for timeseries) in the
   constructor. The instance will listen for any update in ``self._ts``.

For debugging purposes, an attribute ``name`` is used in the base class for
logging. User may choose to provide a name by assigning to the instance
attribute before calling the base class :meth:`Timeseries.__init__` method.

.. note::

   Some object within the Timeseries folder (e.g. CandleStick) has no observable
   to keep track of.  Rather, they act as a source of data for other types of
   Timeseries objects to listen to. Hence, for CandleStick (or other source
   Timeseries), their data source should be constructed by an Event via the
   Event bus architecture.

The base class holds a :class:`~cryptle.metric.base.MemoryTS` and
:class:`~cryptle.metric.base.DiskTS` object. These objects provide the
implementation details of the handling of data.  MemoryTS is responsible for
providing caching utilities for different Timeseries-related objects and also
returns the latest value of the Timeseries.  DiskTS is responsible for clearing
main memory to disk and retrieve from suitable sources the historical values of
the Timeseries when needed.


To access the historical values of any particular valid Timeseries, simply apply
the normal syntax of list-value getting of Python. The values could be
retrievable using the normal python syntax of list value getting, as the
:meth:`~cryptle.metric.base.Timeseries.__getitem__` is implemented accordingly.
So the following works:

.. code:: python

   class FooStrat(Strategy):
      def __init__(self, period):
         self.aggregator = Aggregator(period)
         self.stick = CandleStick(period)
         self.wma = WMA(self.stick.c, 5)

      def retrieveHistory(self):
         # this works as longs as their is sufficient data, would retrieve suitable data
         # from disk/memory appropriately
         hist_vals = self.wma[-20:-5]


Another feature of Timeseries is the decorator
:meth:`~cryptle.metric.base.MemoryTS.cache`.  This decorator can be used on
:meth:`~cryptle.metric.base.Timeseries.evaluate` to provide a local copy of historical
values of the upstream Timeseries, stored in ``self._cache``. The number of items stored
is restricted by ``self._lookback``.

An example of Timeseries might look like:

.. code:: python

   class Foo(Timeseries):
       # For debugging purpose
       def __repr__(self)
           return self.name

       def __init__(self, ts, lookback, name='foo'):
           self.name = name
           super().__init__(ts)
           self._lookback = lookback
           self._ts = ts

       # Generate self._cache for accessing historical self._ts value
       @MemoryTS.cache('normal')
       def evaluate(self):
           # some code that would be updated when ts updates

If a Timeseries is designed to listen to multiple Timeseries objects for updates, the
only supported behaviour of updating is to wait till all the listened timeseries to
update at least once before its :meth:`evaluate` function to run. More sophisticated
control would be implemented if necessary. In this case, the ``self._ts`` attribute
should be set to a list of the Timeseries objects to be listened to:

An optional ``name`` attribute could be defined as mentioned in the previous part.
In this case, the implementation of the :meth:`__repr__` method of the subclass would
make the ``name`` be shown in debugging logs present in the base class level.

.. note::

   The lineralized model of data handling is now employed. That means that along with
   :class:`~cryptle.metric.base.MultivariateTS`, the propgation of data currently does
   not support arbitary operations on direct acyclic graph. Various assumptions are
   being made in modeling the behaviour of propgataion of data flow. In the future,
   these would be improved by implementing the DAG model to the Timeseries update
   propagation.

.. code:: python

   class FooMultiListen(Timeseries):
       def __init__(self, ts1, ts2, lookback):
           self._ts       = ts1, ts2
           self._lookback = lookback
           super().__init__(self._ts)

For any subseries held within a wrapper class intended to be accessed by the
client, a :class:`~cryptle.metric.base.GenericTS` could be declared during the
construction of the wrapper class. The wrapper should be subclassed from
:class:`~cryptle.metric.base.MultivariateTS`. The format of the
:meth:`~cryptle.metric.base.GenericTS.__init__` follows:
``someGenericTS(timeseries_to_be_listened, lookback, eval_func, args)``. The
:meth:`eval_func` should be implemented in the wrapper class and the ``args``
are the arguments that are passed into the :meth:`eval_func`:

.. code:: python

   class fooWrapper(MultivariateTS):
       def __init__(self, *ts, lookback):
           self._lookback = lookback
           def eval_foo1(*args):
                # act as normal evaluate function in Timeseries, to be passed into the GenericTS
                pass

           def eval_foo2(*args, **kwargs):
                # same as above
                pass

           # foo1 and foo2 is the subseries that is held by foo_with_GenereicTS
           self.foo1 = GenericTS(ts, lookback=lookback, eval_func=eval_foo1, args=[self])
           self.foo2 = GenericTS(ts, lookback=lookback, eval_func=eval_foo2, args=[self])
           super().__init__(*ts)

       def evaluate(self):
           self.broadcast()

Notice that the parent :meth:`~cryptle.metric.Timeseries.MultivariateTS.__init__`
is called *after* the construction of the
:class:`~cryptle.metric.base.GenericTS`s. This is necessary for the correct
resolution of Timeseries data propgataion.

The above is analagous of having a :class:`~cryptle.metric.base.Timeseries` with a
:meth:`~eval_func` as its :meth:`~cryptle.metric.base.Timeseries.evaluate` and
passed with with ``args``, constrained by ``lookback`` and listens to updates
specified by the ``ts`` instead of the ``self.ts`` in
:class:`~cryptle.metric.base.Timeseries`.

A :class:`cryptle.metric.Timeseries.MultivariateTS` could be listened to and
publish after all of the objects subclassed from Timeseries updates. It could be
be assigned to the ``self._ts`` of any Timeseries or MultivariateTS.
The effect would be the same as listening to all the constitutent Timeseries of
the wrapper one by one.



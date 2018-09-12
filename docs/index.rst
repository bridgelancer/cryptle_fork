==================
Welcome to Cryptle
==================

Cryptle is a Python algorithmic trading framework. Get started with an overview
with :ref:`overview`, followed by the framework terminlogies and concepts at
:ref:`concepts`. Those who are familiar with the framework can head over
:ref:`advanced` to find specific HOWTO recipes. For Cryptle in detail, the full
reference can be found in the :ref:`api` section.


.. _overview:

Overview
========
Creating a strategy with Cryptle::

   class FooStrat:
      # Todo

The event loop is decoupled from the rest of Cryptle.  Lets see it in action::

   import event

    class Ticker:
        @event.emit('tick')
        def tick(self, val):
            return val

    class Candle:
        @event.on('tick')
        def recv(self, data):
            print(data) 

    ticker = Ticker()
    candle = Candle()

    loop = event.Loop()
    loop.bind(ticker)
    loop.bind(candle)

    ticker.tick(1)  // prints 1 to stdout

Methods decorated as callbacks can still be called normally::

    candle.recv(2)  // prints 2


.. _concepts:

Important Concepts
==================

Event loops allow events to be generated and observed. An event always come with
a data object, though this object can be :code:`None`.

.. note::
   Event name can be any Python valid strings. However the recommended convention
   is 'subject:datatype'. (This is subject to change, since a prototype event
   parser is underway.)


.. _advanced:

Advanced Usage
==============

More dummy text.


.. _api:

API
===

This part of the documentation coveres all the interfaces of Cryptle.


Strategy
--------

.. automodule:: cryptle.strategy

   .. autoclass:: Strategy
      :members: handleTick, handleCandle, handleText, execute

   .. autoclass:: Portfolio
      :members:


Datafeed
--------

.. automodule:: cryptle.datafeed
   :members:


Exchange
--------

.. automodule:: cryptle.exchange
   :members:


Message Bus
-----------

.. automodule:: cryptle.event

   .. autoclass:: Bus
      :members:

   .. autofunction:: on

   .. autofunction:: emit


Backtest
--------

.. automodule:: cryptle.backtest
   :members:


Runtime
-------

.. automodule:: cryptle.runtime
   :members:


Plotting
--------

.. automodule:: cryptle.plotting
   :members:


Orderbook
---------

.. automodule:: cryptle.orderbook
   :members:

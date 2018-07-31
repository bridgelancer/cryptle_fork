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

   from cryptle import Plugin, subscribe, publish

   class FooStrat(Plugin):

      @subscribe('time:15mins')
      def onTime(self, event):
         # Rebalance every 15 minutes
         marketbuy()

      @publish('<pair>:market_buy')
      def buy(self, price):
         return True

To put the strategy to action, install it on an engine::
   from cryptle import engine

   engine.install(FooStrat())


.. _concepts:

Important Concepts
==============

Dummy text.
.. note::
   Event name can be any Python valid strings. However the recommended convention
   is 'subject:datatype'.




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

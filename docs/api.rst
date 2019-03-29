.. _api:

API Reference
=============

This part of the documentation coveres all the interfaces of Cryptle.


Strategy
--------

.. automodule:: cryptle.strategy

   .. autoclass:: Strategy
      :members:

   .. autoclass:: Portfolio
      :members:

   .. autoclass:: TradingStrategy
      :members:
      :undoc-members:

   .. autoclass:: SingleAssetStrategy
      :members:
      :undoc-members:

   .. autoclass:: EventMarketDataMixin
      :members:
      :undoc-members:

   .. autoclass:: EventOrderMixin
      :members:
      :undoc-members:


Event Bus
---------

.. automodule:: cryptle.event

   .. autofunction:: on

   .. autofunction:: source

   .. autoclass:: Bus
      :members:

   .. autoclass:: DeferedSource
      :members:

   .. autoexception:: BusException

   .. autoexception:: ExtraEmit

   .. autoexception:: UnboundEmitter

.. autoclass:: cryptle.clock.Clock


Scheduler
--------

.. automodule:: cryptle.scheduler

   .. autoclass:: Scheduler
      :members:

All actionnames and constraints supported are documented in
:ref:`Scheduler <scheduler_ref>` under User Guides.


Datafeeds
---------
.. Public API of the datafeed package goes here.

.. autofunction:: cryptle.datafeed.connect

Standard
````````
.. py:class:: cryptle.datafeed.Datafeed

   Standard interface of the Datafeed hierarchy. All subclasses of Datafeed
   should implement the following methods.

   .. py:method:: connect()

      Start a thread for a data stream that sends and receives messages.
      Returns nothing.

   .. py:method:: disconnect()

      Stop the data stream and thread. Returns nothing.

   .. py:method:: on(event, callback)

      :param str event: Data stream to listen for.
      :param func callback: Function to be called upon receving the event.

      Register callback for provided events. Generally the most used function.
      Returns nothing.

   .. py:attribute:: connected

      Represents the connection status of the datafeed object.

Bitstamp
````````
.. autoclass:: cryptle.datafeed.Bitstamp
   :members:


Exchanges
---------
.. Public API of the exchange package goes here.

Standard
````````
.. py:class:: crpytle.exchange.Exchange

   Standard interface of the Exchange hierarchy. All subclasses of Exchange
   should implement the following methods.

   .. py:method:: marketBuy(asset, base, amount)

      Place market buy order.

      :param str asset: Asset to be bought.
      :param str base: Currency used for the buy.
      :param float amount: Amount of the asset to buy.
      :rtype: (bool, float)
      :return: Returns two values. First is a boolean indicating a successful
         trade, second is the final execution price.

   .. py:method:: marketSell(asset, base, amount)

      Place market sell order.

      :param str asset: Asset to be bought.
      :param str base: Currency used for the buy.
      :param float amount: Amount of the asset to buy.
      :rtype: (bool, float)
      :return: Returns two values. First is a boolean indicating a successful
         trade, second is the final execution price.

   .. py:method:: limitBuy(asset, base, amount, price)

      Place limit buy order.

      :param str asset: Asset to be bought.
      :param str base: Currency used for the buy.
      :param float amount: Amount of the asset to buy.
      :param float price: Bid price of the limit buy.
      :rtype: (bool, int)
      :return: Returns two values. First is a boolean indicating a successful
         trade, second being the order ID.

   .. py:method:: limitSell(asset, base, amount, price)

      Place limit sell order.

      :param str asset: Asset to be sold.
      :param str base: Currency used for the sell.
      :param float amount: Amount of the asset to sell.
      :param float price: Ask price of the limit sell.
      :rtype: (bool, int)
      :return: Returns two values. First is a boolean indicating a successful
         trade, second being the order ID.

Order
`````
.. members are not autodoc-ed because namedtuple generates unhelpful docs
.. autoclass:: cryptle.exchange.base.Order

Orderbook
`````````
.. autoclass:: cryptle.exchange.base.Orderbook
   :members:

Paper
`````
.. autoclass:: cryptle.exchange.Paper
   :members:

Bitstamp
````````
.. autoclass:: cryptle.exchange.Bitstamp
   :members:


Backtest
--------
Todo.

.. automodule:: cryptle.backtest.backtest
   :members:

.. automodule:: cryptle.backtest.utils
   :members:


Runtime
-------

.. automodule:: cryptle.runtime
   :members:


Plotting
--------

.. automodule:: cryptle.plotting
   :members:


Analytic Orderbook
------------------

.. automodule:: cryptle.orderbook
   :members:


Metric
------

.. automodule:: cryptle.metric.base
   :members:
   :undoc-members:


Logging
-------
.. automodule:: cryptle.logging
   :members:

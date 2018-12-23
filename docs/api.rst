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
      :undoc-members:

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


Datafeed Standard
-----------------

.. autofunction:: cryptle.datafeed.connect

.. py:class:: cryptle.datafeed.Datafeed

   .. py:method:: connect()

      Start a thread for a data stream that sends and receives messages.
      Returns nothing.

   .. py:method:: disconnect()

      Stop the data stream and thread. Returns nothing.

   .. py:method:: on(event, callback)

      Register callback for provided events. Generally the most used function.
      Returns nothing.

   .. py:attribute:: connected

      Represents the connection status of the datafeed object.


Exchange Standard
-----------------

.. py:class:: Exchange

   .. py:method:: marketBuy(asset, base, amount)

      Place market buy order. Returns two values, first being the whether the
      order were successfully placed, second being the average execution price.

      :rtype: (bool, float)

   .. py:method:: marketSell(asset, base, amount)

      Place market sell order. Returns two values, first being the whether the
      order were successfully placed, second being the average execution price.

      :rtype: (bool, float)

   .. py:method:: limitBuy(asset, base, amount, price)

      Place limit buy order.

      :param str asset: Asset to be bought.
      :param str base: Currency used for the buy.
      :param float amount: Amount of the asset to buy.
      :param float price: Bid price of the limit buy.
      :rtype: (bool, int)
      :return: Returns two values, first being the whether the order were
         successfully placed, second being the order id.

   .. py:method:: limitSell(asset, base, amount, price)

      Place limit sell order.

      :param str asset: Asset to be sold.
      :param str base: Currency used for the sell.
      :param float amount: Amount of the asset to sell.
      :param float price: Ask price of the limit sell.
      :rtype: (bool, int)
      :return: Returns two values, first being the whether the order were
         successfully placed, second being the order id.


Paper Exchange
--------------
.. autoclass:: cryptle.exchange.Paper
   :members:
   :undoc-members:

.. autoclass:: cryptle.exchange.paper.Orderbook
   :members:
   :undoc-members:


Registry
--------

.. automodule:: cryptle.registry

   .. autoclass:: Registry
      :members:

All actionnames and constraints supported are documented in
:ref:`Registry <registry_ref>` under User Guides.


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


Metric
------

.. automodule:: cryptle.metric.base
   :members:
   :undoc-members:


Logging
-------
.. automodule:: cryptle.logging
   :members:

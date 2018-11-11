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


Datafeed
--------

.. autofunction:: cryptle.datafeed.connect

.. py:class:: cryptle.datafeed.Datafeed

   .. py:method:: connect() -> None

      Starts a thread for a long-polled socket that sends and receives messages.

   .. py:method:: disconnect() -> None

      Stops the socket and thread.

   .. py:method:: on(event, callback) -> None

      Registers callback for provided events. Generally the most used function.

   .. py:attribute:: connected -> bool

      Returns a boolean for whether the socket is connected to the data source
      server.


Exchange
--------

.. py:class:: Exchange

   .. py:method:: marketBuy(asset: str, base: str, amount: float) -> Tuple[bool, price]

      Place market buy order. Returns two values, first being the whether the
      order were successfully placed, second being the average execution price.

   .. py:method:: marketSell(asset: str, base: str, amount: float) -> Tuple[bool, price]

      Place market sell order. Returns two values, first being the whether the
      order were successfully placed, second being the average execution price.

   .. py:method:: limitBuy(asset: str, base: str, amount: float, price: float) -> Tuple[bool, int]

      Place limit buy order.

      :param str asset: Asset to be bought.
      :param str base: Currency used for the buy.
      :param float amount: Amount of the asset to buy.
      :param float price: Bid price of the limit buy.
      :return: Returns two values, first being the whether the order were
         successfully placed, second being the order id.

   .. py:method:: limitSell(asset: str, base: str, amount: float, price: float) -> Tuple[bool, int]

      Place limit sell order.

      :param str asset: Asset to be sold.
      :param str base: Currency used for the sell.
      :param float amount: Amount of the asset to sell.
      :param float price: Ask price of the limit sell.
      :return: Returns two values, first being the whether the order were
         successfully placed, second being the order id.

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


Timeseries
----------

.. automodule:: metric.base
   :members:

.. _api:

API Reference
=============

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

.. py:class:: Datafeed

   .. py:method:: connect()

      Starts a thread for a long-polled socket that sends and receives messages.

   .. py:method:: disconnect()

      Stops the socket and thread.

   .. py:method:: on(event, callback)

      Registers callback for provided events. Generally the most used function.

   .. py:attribute:: connected

      Boolean for whether the socket is connected to the data source server.


Exchange
--------

.. py:class:: Exchange

   .. py:method:: marketBuy(amount: float)

   .. py:method:: marketSell(amount: float)

   .. py:method:: limitBuy(amount: float, price: float)

   .. py:method:: limitSell(amount: float, price: float)


Registry
--------

.. automodule:: cryptle.registry

   .. autoclass:: Registry
      :members:

All actionnames and constraints supported are documented in
:ref:`Registry <registry_ref>` under User Guides.


Message Bus
-----------

.. automodule:: cryptle.event

   .. autoclass:: Bus
      :members:

   .. autofunction:: on

   .. autofunction:: source

   .. autoclass:: DeferedSource
      :members:

   .. autoexception:: BusException

   .. autoexception:: ExtraEmit

   .. autoexception:: NotListened

   .. autoexception:: UnboundEmitter

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

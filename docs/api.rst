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

   .. autofunction:: source

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
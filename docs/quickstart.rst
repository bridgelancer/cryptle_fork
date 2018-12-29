.. _quickstart:

Quickstart
==========
This document gets you started with Cryptle in 15 minutes by examples. Develop a
strategy, backtest, and deploy it to livetrade with step-by-step explanations.

A minimal strategy
------------------
Say one day you have the ingenious idea of buying BTC whenever it goes over
$200 and selling it whenever it's above $400. The simplest way to codify that in
plain python is::

    def winning_strategy(self, price):
        if price > 200:
            # buy
        if price < 400:
            # sell


While the function above can already fully encapsulate the business logic of our
strategy, Cryptle can only run strategies that are written as a
:class:`~cryptle.strategy.Strategy` object. Let's do exactly that::

    from cryptle.strategy import SingleAssetStrat

    class BTCStrat(SingleAssetStrat):
        def winning_strategy(self, price):
            ...

We created a Strategy
The next we would need is a data source.


Another core mechanicism in Cryptle is the :ref:`Event Bus <events>`.


.. _quick_backtest:

Backtesting
-----------
Todo.

Helper functions
````````````````
The :mod:`~cryptle.backtest` module has many helper functions to
backtest strategies of various types of financial data. The

::

    import json
    from cryptle.backtest import backtest_with_bus

    strat = BTCStrat()
    backtest_with_bus(strat, data)


.. _quick_livetrade:

Livetrade
---------
The last section left you off with a strategy that has been backtested and has
shown promising returns. If you haven't yet seen the backtesting tutorial, it
goes through several key components in the Cryptle that will be skipped in this
document, So please first go through that if you're not familiar with the
framework.

Now that you have the killer strategy that's been proven to work by historical
data, you just need to hook it up to streamed live-data and to an exchange for
placing buy/sell orders.


Streaming live-data
```````````````````
Cryptle provides a number of data sources out of the box, most of which are
cryptocurrency market data. Let us start with an example using the bitstamp
exchange data source:::

    from cryptle.datafeed import Bitstamp as Feed

    feed = Feed()
    feed.connect()
    feed.on('trades:btcusd', winning_strategy)

Here's what we've done:

1. First we import :class:`~cryptle.datafeed.Bitstamp` which is a subclass of :class:`~cryptle.base.Datafeed`.
2. Then we create an instance of this class.
3. Establish connection to the data server.
4. We use :meth:`~cryptle.base.Datafeed.on` to setup :code:`winning_strategy` as a callback for
   the ``trades:btcusd`` event.


Placing orders
``````````````
The next thing to do is actually send our orders to an exchange:::

    from cryptle.exchange import Bitstamp
    exchange = Bitstamp()

We will also have to keep track of our portfolio on the exchange. Make let's
make a few calls

.. note::

   Depending on your exchange, your portfolio status might be available as a
   data stream which would be accessed through a :class:`Datafeed` instance.


Refactor
````````
The number calls to ``bind()`` is starting to fill most of the code. We've also
used global variables to keep track of our portfolio. Lets refactor all of this
and bundle the strategy into a class:::

    class Strat(Strategy):
        def __init__(self):
            # todo

        @on('trades:btcusd')
        def determine():
           if xxx
            self.buy(amount)

        @source('')

Summary
-------
Here's a polished version of the sample script that may appear in production:::

    from cryptle.event import source, on, Bus
    from cryptle.datafeed import Bitstamp as Feed
    from cryptle.exchange import Bitstamp as Exchange

    class Strat(StrateMixin):
        def __init__(self):
            # todo

        @on('trades:btcusd')
        def determine():
           if xxx
            self.buy(amount)


    if __name__  == "__main__":
        bus      = Bus()
        feed     = Feed()
        strat    = Strat()
        exchange = Exchange()

        bus.bind(feed)
        bus.bind(strat)
        bus.bind(exchange)

        feed.connect()
        feed.broadcast('trades:btcusd')

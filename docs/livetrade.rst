.. _livetrade:

Livetrade
=========
This page is a continuation of the :doc:`backtesting <quickstart>` tutorial.
The previous guide left you off with a strategy that has been backtested and has
shown promising returns. If you haven't yet seen the backtesting tutorial, it
goes through several key components in the Cryptle that will be skipped in this
document, So please first go through that if you're not familiar with the
framework.

Now that you have the killer strategy that's been proven to work by historical
data, you just need to hook it up to streamed live-data and to an exchange for
placing buy/sell orders.


Streaming live-data
----------------
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
   the :code:`trades:btcusd` event.


Placing orders
------------
The next thing to do is actually send our orders to an exchange:::

    from cryptle.exchange import Bitstamp
    exchange = Bitstamp()

We will also have to keep track of our portfolio on the exchange. Make let's
make a few calls

.. note::
   Depending on your exchange, your portfolio status might be available as a
   data stream which would be accessed through a :class:`Datafeed` instance.


Refactor
--------
The number calls to `bind()` is starting to fill most of the code. We've also
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

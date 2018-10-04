.. _livetrade:

Livetrade
=========
This page is a 5 minute tutorial of livetrading with Cryptle. You will be
accompanied by step-by-step explanation of the examples, with a polished
script at the end.

Say one day you have the ingenious idea of buying BTC whenever it goes over
$200 and selling it whenever it's above $400. Let's put that to action with
code:::

    def winning_strategy(self, price):
        if price > 200:
            # buy
        if price < 400:
            # sell

Now that's you have this killer strategy, you just need to hook it up to the
exchange for streamed real time data and to place buy/sell orders.


Stream live data
----------------
Cryptle framework to the rescue. Let us start with the importing a data source:::

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


Place orders
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

    class Strat(StrateMixin):
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

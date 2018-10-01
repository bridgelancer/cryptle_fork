.. _quickstart:

Quickstart
==========
This page is a 5 minute tutorial, of Cryptle. Here you will be accompanied by 
step-by-step explanation of the examples, and brief mentions to critical
components in Cryptle.


Create and test a strategy with Cryptle::

    from cryptle.event import source, on, Bus
    from cryptle.datafeed import Bitstamp as Feed
    from cryptle.exchange import Bitstamp as Exchange

    class Strat:
        @on('trades:btcusd')
        def handle(self, data):
            price = data['price']
            if price > 1000:
                self.buy()

        @source('buy:btcusd')
        def buy(self, price):
            return price

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

Todo.



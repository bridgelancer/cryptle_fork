import time
import pytest
import cryptle.datafeed as fd


TRADE_BTC = 'trades:btcusd'
TRADE_ETH = 'trades:ethusd'


def test_bitstamp():
    def cb(msg):
        print(msg)

    feed = fd.BitstampFeed()
    feed.connect()
    feed.on(TRADE_BTC, cb)
    feed.on(TRADE_ETH, cb)
    time.sleep(5)


def feed_bitfinex():
    def cb(msg):
        print(msg)

    feed = fd.BitfinexFeed()
    feed.connect()
    feed.on(TRADE_BTC, cb)
    feed.on(TRADE_ETH, cb)
    time.sleep(5)

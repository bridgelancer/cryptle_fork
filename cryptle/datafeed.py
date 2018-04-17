import logging
import time
import json
from contextlib import contextmanager

import pysher


# @Todo refactor this into a method of each feed class
@contextmanager
def connect(feed_name, *args, **kwargs):
    '''Datafeed as context manager.'''
    try:
        if feed_name == 'bitstamp':
            feed = BitstampFeed()
            feed.connect(*args, **kwargs)
        else:
            raise ValueError('No datafeed named {}'.format(feed_name))
        yield feed
    finally:
        feed.close()


class Datafeed:
    '''Base class for datafeed objects'''
    pass


class BitstampFeed(Datafeed):
    '''Datafeed for bitstamp, has dependency on pysher websockets.

    Provides a javascript-like interface for various types of supported bitstamp
    events. Details are provided at https://www.bitstamp.net/websocket/

    Note:
        Dependent on a recent version of pysher. Otherwise 4200 disconnects
        will lead to channels being no longer recognised and requires a re-binding
        of callbacks.
    '''
    key = 'de504dc5763aeef9ff52'

    def __init__(self, log_level=logging.INFO):
        self.pusher = pysher.Pusher(self.key, log_level=log_level, auto_sub=True)


    def connect(self):
        self.pusher.connect()
        time.sleep(1)


    def close(self):
        self.pusher.disconnect()


    def isConnected(self):
        return self.pusher.connection.is_alive()


    def onTrade(self, asset, base_currency, callback):
        channel = 'live_trades' + self._encode_pair(asset, base_currency)
        self._bindSocket(channel, 'trade', lambda x: callback(json.loads(x)))


    def onOrderCreate(self, asset, base_currency, callback):
        channel = 'live_orders' + self._encode_pair(asset, base_currency)
        self._bindSocket(channel, 'order_created', lambda x: callback(json.loads(x)))


    def onOrderChanged(self, asset, base_currency, callback):
        channel = 'live_orders' + self._encode_pair(asset, base_currency)
        self._bindSocket(channel, 'order_changed', lambda x: callback(json.loads(x)))


    def onOrderDeleted(self, asset, base_currency, callback):
        channel = 'live_orders' + self._encode_pair(asset, base_currency)
        self._bindSocket(channel, 'order_deleted', lambda x: callback(json.loads(x)))


    def onOrderBookUpdate(self, asset, base_currency, callback):
        channel = 'order_book' + self._encode_pair(asset, base_currency)
        self._bindSocket(channel, 'data', lambda x: callback(json.loads(x)))


    def onOrderBookDiff(self, asset, base_currency, callback):
        channel = 'diff_order_book' + self._encode_pair(asset, base_currency)
        self._bindSocket(channel, 'data', lambda x: callback(json.loads(x)))


    def _bindSocket(self, channel_name, event, callback):
        if channel_name not in self.pusher.channels:
            self.pusher.subscribe(channel_name)

        channel = self.pusher.channels[channel_name]
        channel.bind(event, callback)


    @staticmethod
    def _encode_pair(asset, base_currency):
        if asset == 'btc' and base_currency == 'usd':
            return ''
        else:
            return '_' + asset + base_currency

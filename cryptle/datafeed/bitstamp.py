import logging
import time
import json
import contextlib

import pysher

from .exception import *


# @Todo refactor this into a method of each feed class
@contextlib.contextmanager
def connect(feed_name, *args, **kwargs):
    """Datafeed as context manager."""
    try:
        if feed_name == 'bitstamp':
            feed = BitstampFeed()
            feed.connect(*args, **kwargs)
        else:
            raise ValueError('No datafeed named {}'.format(feed_name))
        yield feed
    finally:
        feed.close()


def decode_event(event):
    """Parse event string in cryptle representation into bitstamp representation."""

    channel, *params = event.split(':')
    if channel == 'trades':
        bs_chan  = 'live_trades'
        bs_event = 'trade'

    elif channel == 'bookchange':
        bs_chan  = 'live_orders'
        bs_event = 'order_changed'

    elif channel == 'bookcreate':
        bs_chan  = 'live_orders'
        bs_event = 'order_created'

    elif channel == 'bookdelete':
        bs_chan  = 'live_orders'
        bs_event = 'order_deleted'

    elif channel == 'bookdiff':
        bs_chan  = 'diff_order_book'
        bs_event = 'data'

    else:
        raise BadEvent(event)

    # quickfix for stupid bitstamp legacy API
    pair = params.pop(0)
    if pair != 'btcusd':
        bs_chan += '_' + pair

    return bs_chan, bs_event, params


def encode_event():
    pass


class BitstampFeed:
    """Datafeed for bitstamp, has dependency on pysher websockets.

    Provides a javascript-like interface for various types of supported bitstamp
    events. Details are provided at https://www.bitstamp.net/websocket/

    Note:
        Dependent on a recent version of pysher. Otherwise 4200 disconnects
        will lead to channels being no longer recognised and requires a re-binding
        of callbacks.
    """
    key = 'de504dc5763aeef9ff52'

    def __init__(self, log_level=logging.INFO):
        self.pusher = pysher.Pusher(self.key, log_level=log_level, auto_sub=True)

    # ----------
    # Public interface
    # ----------
    def connect(self):
        self.pusher.connect()

    def close(self):
        self.pusher.disconnect()

    @property
    def connected(self):
        return self.pusher.connection.is_alive()

    def on(self, event, cb):
        channel, event, *args = decode_event(event)
        self._bindSocket(channel, event, cb)

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

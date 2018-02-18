import logging
import time
import json

import pysher

from cryptle.utility import *

logger = logging.getLogger(__name__)


class BitstampFeed:
    '''Datafeed interface for bitstamp, based on websockets provided by pysher.

    Provides a javascript-like interface for various types of supported bitstamp events. Details are
    provided at https://www.bitstamp.net/websocket/

    Note: Dependent on a recent version of pysher. Otherwise 4200 disconnects will lead to channels
        being no longer recognised and requires a re-binding of callbacks.
    '''
    key = 'de504dc5763aeef9ff52'

    def __init__(self, auto_connect=True, log_level=logging.INFO):
        self.pusher = pysher.Pusher(self.key, log_level=log_level, auto_sub=True)

        if auto_connect:
            self.connect()


    def connect(self):
        self.pusher.connect()
        time.sleep(1)


    def disconnect(self):
        self.pusher.disconnect()


    def isConnected(self):
        return self.pusher.connection.is_alive()

    @staticmethod
    def _encode_pair(asset, base_currency):
        if asset == 'btc' and base_currency == 'usd':
            return ''
        else:
            return asset + '_' + base_currency


    def onTrade(self, asset, base_currency, callback):
        assert callable(callback)

        channel = 'live_trades' + self._encode_pair(asset, base_currency)
        self._bindSocket(channel, 'trade', lambda x: callback(json.loads(x)))


    def onOrderCreate(self, asset, base_currency, callback):
        assert callable(callback)

        channel = 'live_orders' + self._encode_pair(asset, base_currency)
        self._bindSocket(channel, 'order_created', lambda x: callback(json.loads(x)))


    def onOrderChanged(self, asset, base_currency, callback):
        assert callable(callback)

        channel = 'live_orders' + self._encode_pair(asset, base_currency)
        self._bindSocket(channel, 'order_changed', lambda x: callback(json.loads(x)))


    def onOrderDeleted(self, asset, base_currency, callback):
        assert callable(callback)

        channel = 'live_orders' + self._encode_pair(asset, base_currency)
        self._bindSocket(channel, 'order_deleted', lambda x: callback(json.loads(x)))


    def onOrderBookUpdate(self, asset, base_currency, callback):
        assert callable(callback)

        channel = 'order_book' + self._encode_pair(asset, base_currency)
        self._bindSocket(channel, 'data', lambda x: callback(json.loads(x)))


    def onOrderBookDiff(self, asset, base_currency, callback):
        assert callable(callback)

        channel = 'diff_order_book' + self._encode_pair(asset, base_currency)
        self._bindSocket(channel, 'data', lambda x: callback(json.loads(x)))


    def _bindSocket(self, channel_name, event, callback):
        if channel_name not in self.pusher.channels:
            self.pusher.subscribe(channel_name)

        channel = self.pusher.channels[channel_name]
        channel.bind(event, callback)


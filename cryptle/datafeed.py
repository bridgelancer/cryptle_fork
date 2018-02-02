from cryptle.utility import *
import json
import time
import pysher
import logging
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


    def onTrade(self, pair, callback):
        assert isinstance(pair, str)
        assert callable(callback)

        if pair == 'btcusd':
            self._bindSocket('live_trades', 'trade', lambda x: callback(json.loads(x)))
        else:
            self._bindSocket('live_trades_' + pair, 'trade', lambda x: callback(json.loads(x)))


    def onOrderCreate(self, pair, callback):
        assert isinstance(pair, str)
        assert callable(callback)

        if pair == 'btcusd':
            self._bindSocket('live_trades', 'order_created', lambda x: callback(json.loads(x)))
        else:
            self._bindSocket('live_orders_' + pair, 'order_created', lambda x: callback(json.loads(x)))


    def onOrderChanged(self, pair, callback):
        assert isinstance(pair, str)
        assert callable(callback)

        if pair == 'btcusd':
            self._bindSocket('live_trades', 'order_changed', lambda x: callback(json.loads(x)))
        else:
            self._bindSocket('live_orders_' + pair, 'order_changed', lambda x: callback(json.loads(x)))


    def onOrderDeleted(self, pair, callback):
        assert isinstance(pair, str)
        assert callable(callback)

        if pair == 'btcusd':
            self._bindSocket('live_orders', 'order_deleted', lambda x: callback(json.loads(x)))
        else:
            self._bindSocket('live_orders_' + pair, 'order_deleted', lambda x: callback(json.loads(x)))


    def onOrderBookUpdate(self, pair, callback):
        assert isinstance(pair, str)
        assert callable(callback)

        if pair == 'btcusd':
            self._bindSocket('order_book', 'data', lambda x: callback(json.loads(x)))
        else:
            self._bindSocket('order_book_' + pair, 'data', lambda x: callback(json.loads(x)))


    def onOrderBookDiff(self, pair, callback):
        assert isinstance(pair, str)
        assert callable(callback)

        if pair == 'btcusd':
            self._bindSocket('diff_order_book', 'data', lambda x: callback(json.loads(x)))
        else:
            self._bindSocket('diff_order_book_' + pair, 'data', lambda x: callback(json.loads(x)))


    def _bindSocket(self, channel_name, event, callback):

        if channel_name not in self.pusher.channels:
            self.pusher.subscribe(channel_name)

        channel = self.pusher.channels[channel_name]
        channel.bind(event, callback)


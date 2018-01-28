import time
import pysher
import logging
logger = logging.getLogger(__name__)


class BitstampFeed:
    key = 'de504dc5763aeef9ff52'

    def __init__(self, auto_connect=True, log_level=logging.INFO):
        self.pusher = pysher.Pusher(self.key, log_level=log_level)

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
            self._bindSocket('live_trades', 'trade', callback)
        else:
            self._bindSocket('live_trades_' + pair, 'trade', callback)


    def onOrderCreate(self, pair, callback):
        assert isinstance(pair, str)
        assert callable(callback)

        if pair == 'btcusd':
            self._bindSocket('live_orders', 'order_created', callback)
        else:
            self._bindSocket('live_orders_' + pair, 'order_created', callback)


    def onOrderChanged(self, pair, callback):
        assert isinstance(pair, str)
        assert callable(callback)

        if pair == 'btcusd':
            self._bindSocket('live_orders', 'order_changed', callback)
        else:
            self._bindSocket('live_orders_' + pair, 'order_changed', callback)


    def onOrderDeleted(self, pair, callback):
        assert isinstance(pair, str)
        assert callable(callback)

        if pair == 'btcusd':
            self._bindSocket('live_orders', 'order_deleted', callback)
        else:
            self._bindSocket('live_orders_' + pair, 'order_deleted', callback)


    def onOrderBookUpdate(self, pair, callback):
        assert isinstance(pair, str)
        assert callable(callback)

        if pair == 'btcusd':
            self._bindSocket('order_book', 'data', callback)
        else:
            self._bindSocket('order_book_' + pair, 'data', callback)


    def onOrderBookDiff(self, pair, callback):
        assert isinstance(pair, str)
        assert callable(callback)

        if pair == 'btcusd':
            self._bindSocket('diff_order_book', 'data', callback)
        else:
            self._bindSocket('diff_order_book_' + pair, 'data', callback)


    def _bindSocket(self, channel_name, event, callback):

        if channel_name not in self.pusher.channels:
            self.pusher.subscribe(channel_name)

        channel = self.pusher.channels[channel_name]
        channel.bind(event, callback)


import time
import pysher

class BitstampFeed:

    def __init__(self):
        api_key = 'de504dc5763aeef9ff52'

        self.pusher = pysher.Pusher(api_key)
        self.pusher.connect()
        time.sleep(2)


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


    def _bindSocket(self, channel_name, event, callback):

        if channel_name not in self.pusher.channels:
            self.pusher.subscribe(channel_name)

        channel = self.pusher.channels[channel_name]
        channel.bind(event, callback)


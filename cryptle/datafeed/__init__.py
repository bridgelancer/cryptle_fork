import contextlib

from cryptle.event import source, on, DeferedSource
from .bitstamp import BitstampFeed
from .bitfinex import BitfinexFeed
from .exception import *


# Module level constants for supported datafeeds
BITSTAMP = 'bitstamp'
BITFINEX = 'bitfinex'

BITSTAMP_FEED = 'bitstamp_feed'
BITFINEX_FEED = 'bitfinex_feed'


@contextlib.contextmanager
def connect(feed_name, *args, **kwargs):
    """Datafeed as context manager."""
    try:
        if feed_name == BITSTAMP:
            feed = Bitstamp()
            feed.connect(*args, **kwargs)

        elif feed_name == BITFINEX:
            feed = Bitfinex()
            feed.connect(*args, **kwargs)

        elif feed_name == BITSTAMP_FEED:
            feed = BitstampFeed()
            feed.connect(*args, **kwargs)

        elif feed_name == BITFINEX_FEED:
            feed = BitfinexFeed()
            feed.connect(*args, **kwargs)

        else:
            raise ValueError('No datafeed named {}'.format(feed_name))
        yield feed
    finally:
        feed.disconnect()


class Bitstamp(BitstampFeed, DeferedSource):
    """Simple wrapper around BitstampFeed to emit data into a bus."""

    def broadcast(self, event):
        @self.source(event)
        def _emit(data):
            return data

        self.on(event, _emit)


class Bitfinex(BitfinexFeed, DeferedSource):
    """Simple wrapper around BitstampFeed to emit data into a bus."""

    def broadcast(self, event):
        @self.source(event)
        def _emit(data):
            return data

        self.on(event, _emit)

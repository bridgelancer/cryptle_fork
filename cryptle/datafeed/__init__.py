import contextlib

from cryptle.event import source, on, DeferedSource
from .bitstamp import BitstampFeed
from .bitfinex import BitfinexFeed
from .exception import *


# Module level constants for supported datafeeds
BITSTAMP = 'bitstamp'
BITFINEX = 'bitfinex'

BITSTAMP_EMITTER = 'bitstamp_emitter'
BITFINEX_EMITTER = 'bitfinex_emitter'


@contextlib.contextmanager
def connect(feed_name, *args, **kwargs):
    """Datafeed as context manager."""
    try:
        if feed_name == BITSTAMP:
            feed = BitstampFeed()
            feed.connect(*args, **kwargs)

        elif feed_name == BITFINEX:
            feed = BitfinexFeed()
            feed.connect(*args, **kwargs)

        elif feed_name == BITSTAMP_EMITTER:
            feed = BitstampEmitter(args.pop(0))
            feed.connect(*args, **kwargs)

        elif feed_name == BITSTAMP_EMITTER:
            # Todo_events
            feed = BitfinexFeed()
            feed.connect(*args, **kwargs)

        else:
            raise ValueError('No datafeed named {}'.format(feed_name))
        yield feed
    finally:
        feed.close()


class BitstampEmitter(BitstampFeed, DeferedSource):
    """Simple wrapper around BitstampFeed to emit data into a bus."""
    def broadcast(self, event):
        @self.source(event)
        def _emit(data):
            return data
        self.on(event, _emit)

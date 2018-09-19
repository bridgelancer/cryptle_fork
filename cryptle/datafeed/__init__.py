import contextlib

import cryptle.event as event
from .bitstamp import BitstampFeed
from .bitfinex import BitfinexFeed
from .exception import *


# Module level constants for supported datafeeds
BITSTAMP = 'bitstamp'
BITFINEX = 'bitfinex'


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

        else:
            raise ValueError('No datafeed named {}'.format(feed_name))
        yield feed
    finally:
        feed.close()

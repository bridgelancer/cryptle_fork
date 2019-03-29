import logging
import datetime as dt
import queue
import time
import warnings

import pytest

from cryptle.lib.ib import IBConnection, IBExchange, IBDatafeed
from cryptle.lib.ib import PACKAGE_LOGGER_NAME
from cryptle.exchange import MarketOrderFailed


logging.basicConfig(level=logging.DEBUG, format="%(name)s: [%(levelname)s] %(message)s")
logging.getLogger('ibrokers').setLevel(logging.INFO)
logging.getLogger('ibrokers.client').setLevel(logging.DEBUG)
# logging.getLogger('ibrokers.wrapper').setLevel(logging.DEBUG)

# Avoid clashing with clients in production
IB_CLIENT_ID = 9
HKT = dt.timezone(dt.timedelta(hours=8))

DEFAULT_ASSET = 'hsi'
DEFAULT_BASE = 'hkd'
DEFAULT_CONTRACT = DEFAULT_ASSET + DEFAULT_BASE


def hkex_trading():
    now = dt.datetime.now(tz=HKT)
    _time = now.time()
    _date = now.date()
    return (
        (9 < _time.hour and _time.hour < 12) or (13 < _time.hour and _time.hour < 16)
    ) and (_date.weekday() in range(5))


@pytest.fixture(scope='module')
def ib_connection():
    conn = IBConnection()
    conn.connect(client_id=IB_CLIENT_ID)
    yield conn
    conn.disconnect()


@pytest.fixture(scope='module')
def datafeed(ib_connection):
    yield IBDatafeed(ib_connection)


@pytest.fixture(scope='module')
def exchange(ib_connection):
    yield IBExchange(ib_connection)


@pytest.fixture(autouse=True, scope='function')
def sleep():
    time.sleep(1)


def test_connection():
    conn = IBConnection()
    conn.connect(client_id=IB_CLIENT_ID)
    assert conn.isConnected()
    conn.disconnect()
    assert not conn.isConnected()


def test_exchange_basic(exchange):
    next_id = exchange._nextOrderId()
    assert isinstance(next_id, int)


@pytest.mark.skipif(not hkex_trading(), reason='Out HKEX trading hours')
def test_exchange_order(exchange):
    exchange.max_timeout = 5
    exchange.max_retry = 3

    try:
        assert exchange.marketSell('hsi', 'hkd', 7.0)
    except MarketOrderFailed as e:
        warnings.warn(UserWarning(f'Market order {e.id} failed. Is the market closed?'))
        exchange.cancelOrder(e.id)

    try:
        assert exchange.marketBuy('tsla', 'usd', 100.0)
    except MarketOrderFailed as e:
        warnings.warn(UserWarning(f'Market order {e.id} failed. Is the market closed?'))
        exchange.cancelOrder(e.id)


@pytest.mark.skipif(not hkex_trading(), reason='Out HKEX trading hours')
def test_datafeed_marketdata(datafeed):
    class TickCallback:
        def __init__(self):
            self.q = queue.Queue()

        def __call__(*args, **kwargs):
            logging.debug('Tick CB called')
            self.q.put((args, kwargs))

    retry = 0
    max_retry = 5
    cb = TickCallback()
    datafeed.onTrade('hsi', 'hkd', cb)
    while retry < max_retry:
        try:
            cb.q.get(timeout=5)
        except queue.Empty:
            retry += 1
            logging.debug('Retrying get market data...')
        else:
            return
    warnings.warn(UserWarning('Recieved no market data. Is the market closed?'))

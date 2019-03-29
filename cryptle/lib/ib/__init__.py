"""This module provide abstractions of IB API to adapt to Cryptle."""

import collections
import functools
import logging
import queue
import threading
import time
import warnings

from .client import EClient
from .wrapper import EWrapper
from .order import Order
from .utils import parent_fn_context
from .mappers import ASSET_CONTRACT_MAP, OrderStatus, OrderType, TWSEvent

from .common import PACKAGE_LOGGER_NAME

from cryptle.exchange import MarketOrderFailed


logger = logging.getLogger(__name__)


class IBConnection(EClient, EWrapper):
    """Facade of connection routines to IB TWS.

    This class thinly composes the out-of-the-stock EClient and EWrapper. To further
    listen to EWrapper callbacks, higher level classes can overwrite the EWrapper
    methods either by inheritance or monkey patched composition.
    """

    _next_client_id = 0
    _next_req_id = 0

    # monkey patch all EWrapper interfaces to call registered callbacks
    @staticmethod
    def patch(method, event):
        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            method(self, *args, **kwargs)
            listeners = self._listeners[event]
            logger.debug(f'Event {event} has {len(listeners)} listeners')
            if len(listeners) > 0:
                for listener in listeners:
                    logger.debug(f'Calling listener {listener} of {event}')
                    listener(*args, **kwargs)

        return wrapper

    def __init__(self):
        EClient.__init__(self, self)
        self._error_handlers = collections.defaultdict(list)
        self._listeners = collections.defaultdict(list)
        self.client_id = None

    def connect(self, host='127.0.0.1', port=7497, client_id=None):
        if client_id is None:
            client_id = self._next_client_id
            IBConnection._next_client_id += 1
        self.client_id = client_id

        # blocking call
        super().connect(host, port, client_id)

        # turns the blocking EClient.run() into background thread
        thread = threading.Thread(target=self.run)
        thread.start()
        self.thread = thread

    def disconnect(self):
        super().disconnect()
        self.thread.join()

    def __repr__(self):
        return f'{self.__class__.__qualname__}(id={self.client_id})'

    def error(self, reqId: int, errorCode: int, errorString: str):
        """Overwrite EWrapper.error() to allow custom error hooks."""
        if len(self._error_handlers[errorCode]) > 0:
            for handler in self._error_handlers[errorCode]:
                logger.debug(f'Calling TWS error handler {handler} of {errorCode}')
                handler(reqId, errorString)
        else:
            super().error(reqId, errorCode, errorString)

    def onError(self, errCode, cb):
        self._error_handlers[errCode].append(cb)

    def on(self, event: TWSEvent, callback: callable):
        """Enable runtime custom hooks to TWS Events."""
        if event in TWSEvent:
            self._listeners[event].append(callback)

    def getReqId(self):
        """Return a request ID. Note it's different from Order Id."""
        rid = self._next_req_id
        self._next_req_id += 1
        return rid


# Invoke patch on EWrapper only. Methods from IBConnection should still override
for event in TWSEvent:
    method = getattr(EWrapper, event.name)
    setattr(EWrapper, event.name, IBConnection.patch(method, event))


def _put_to_queue(queue):
    def _putter(*args, **kwargs):
        # puts a tuple
        queue.put((args, kwargs))

    return _putter


def makeContract(asset, base):
    return ASSET_CONTRACT_MAP[asset + base]


def makeOrder(order_type: OrderType, amount):
    if amount == 0:
        raise ValueError('Order cannot have 0 quantity')
    order = Order()
    order.action = 'BUY' if amount > 0 else 'SELL'
    order.orderType = order_type.value
    order.totalQuantity = abs(amount)
    return order


class IBExchange:
    """Adaptor from an IBConnection to a Cryptle compliant exchange.

    Args
    ----
    conn : IBConnection
        A connection object to handling connecting with IB TWS.
    """

    def __init__(self, conn: IBConnection):
        self.conn = conn
        self.max_timeout = 5
        self.max_retry = 5
        self._last_order_id = -1
        self._oid = -1
        self._pending_cancels = set()

        # these queues are all synchronization primitives
        self.orderid_queue = queue.Queue()
        self.conn.on(TWSEvent.nextValidId, _put_to_queue(self.orderid_queue))

        self.order_queue = queue.Queue()
        self.conn.on(TWSEvent.orderStatus, _put_to_queue(self.order_queue))

        self.conn.onError(201, self._checkReject)

        self.cancel_queue = queue.Queue()
        self.conn.onError(202, _put_to_queue(self.cancel_queue))

    # === Queue direct consumers ===
    def _nextOrderId(self):
        self.conn.reqIds()
        ((oid,), _) = self.orderid_queue.get(timeout=self.max_timeout)
        logger.debug('-- QUEUE -- %s() %r', 'nextOrderId', oid)

        if self._last_order_id != oid:
            self._last_order_id = oid
            self._oid = self._last_order_id
            return oid
        else:
            self._oid += 1
            logger.debug('Duplicate Order ID from TWS, using %d', self._oid)
            return self._oid

    def _pollOrderStatus(self, oid) -> OrderStatus:
        self.conn.reqOpenOrders()
        args, _ = self.order_queue.get(timeout=self.max_timeout)
        logger.debug('-- QUEUE -- %s() %r', 'orderStatus', args)

        # partially extract args
        order_id, status, *_ = args
        # todo: else put the order back in the queue, will need for limit orders
        if order_id == oid:
            return OrderStatus(status)

    # === Internals ===
    def _pollOrderStatusTillFilled(self, oid):
        retry = 0
        while retry < self.max_retry:
            logger.debug('polling try: %d', retry)
            state = self._pollOrderStatus(oid)
            if state == OrderStatus.FILLED:
                return True
            elif state == OrderStatus.API_PENDING:
                pass
            else:
                retry += 1
        logger.debug('reached max order status polling retries')
        return False

    def syncPlaceOrder(self, contract, order):
        oid = self._nextOrderId()
        order.orderId = oid
        self.conn.placeOrder(oid, contract, order)
        # blocks until the market order is confirmed to have succeed or failed
        success = self._pollOrderStatusTillFilled(oid)
        if not success:
            raise MarketOrderFailed(oid)
        else:
            return oid

    def _checkReject(self, oid, reason):
        warnings.warn(f'Order {oid}: {reason}')

    # === Cryptle standard interface ===
    def marketBuy(self, asset, base, amount) -> int:
        """
        Args
        ----
        asset: str, Name of asset
        base: str, Name of trade pair
        amount: float, Buy amount

        Returns
        ------
        Order ID
        """
        contract = makeContract(asset, base)
        order = makeOrder(OrderType.MARKET, amount)
        return self.syncPlaceOrder(contract, order)

    def marketSell(self, asset, base, amount) -> int:
        """
        Args
        ----
        asset: str, Name of asset
        base: str, Name of trade pair
        amount: float, Sell amount

        Returns
        ------
        Order ID
        """
        contract = makeContract(asset, base)
        order = makeOrder(OrderType.MARKET, -amount)
        return self.syncPlaceOrder(contract, order)

    def cancelOrder(self, oid):
        self.conn.cancelOrder(oid)
        self._pending_cancels.add(oid)
        try:
            (rec_oid,), reason = self.cancel_queue.get(timeout=10)
            logger.debug('-- QUEUE -- %s() %s', 'cancelOrder', rec_oid)
        except queue.Empty:
            return False
        else:
            if rec_oid in self._pending_cancels and rec_oid == oid:
                self._pending_cancels.remove(oid)
                return True
            else:
                logger.error('Order %d cancelled unexpectedly', rec_oid, reason)
                return True


class IBDatafeed:
    """Adaptor from an IBConnection to a Cryptle compliant datafeed.

    Args
    ----
    conn : IBConnection
        A connection object to handling connecting with IB TWS.
    """

    def __init__(self, conn):
        self.conn = conn
        self.tick_callbacks = collections.defaultdict(list)

    def onTrade(self, asset, base, callback):
        """
        Args
        ----
        callback : Callable
            Function that takes (time, price, size) as argument.
        """
        # IB EClient tick data request parameters
        TICK_TYPE = 'AllLast'
        NUM_TICKS = 0  # this is number of historical ticks to get on top of new ones
        IGNORE_SIZE = False  # dunno what this is

        rid = self.conn.getReqId()
        pair = asset + base
        contract = makeContract(asset, base)
        self.tick_callbacks[rid] = callback
        self.conn.on(TWSEvent.tickByTickAllLast, self._adaptTickByTickAllLast)
        self.conn.reqTickByTickData(rid, contract, TICK_TYPE, NUM_TICKS, IGNORE_SIZE)

    def _adaptTickByTickAllLast(
        self, reqId, tickType, time, price, size, attribs, exchange, specialConditions
    ):
        # delegates to the eclient thread
        self.tick_callbacks[reqId](time, price, size)


VERSION = {'major': 9, 'minor': 73, 'micro': 7}


def get_version_string():
    version = '{major}.{minor}.{micro}'.format(**VERSION)
    return version


__version__ = get_version_string()

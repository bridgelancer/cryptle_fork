import bisect
import logging
from collections import defaultdict

from cryptle.event import source, on
from cryptle.orderbook import Orderbook
from .exception import ExchangeError, OrderError


_LOG = logging.getLogger(__name__)


class Orderbook:
    """In memory orderbook with order IDs optimized for paper trading.

    Args:
        time: (optional) Start time of the orderbook

    See also:
        This is a single trading instrument orderbook. For a full treatment for
        papertrading, see :class:`Paper`.
    """
    def __init__(self, time=0):
        self.bid_prices = []
        self.ask_prices = []

        self._order_id = 0
        self._open_orders = {}

        self._bids = defaultdict(set)
        self._asks = defaultdict(set)
        self._orders = {}

    def __repr__(self):
        return '<{}({} bids, {} asks)>'.format(
            self.__qualname__,
            len(self._bids),
            len(self._asks),
        )

    def create_bid(self, amount: float, price: float):
        if price > self._last_price:
            raise ValueError('Bid price > top ask price')

        oid = self._new_order(price, amount)
        if price not in self.bid_prices:
            bisect.insort(self.bid_prices, price)
            self._bids[price].add(oid, )
        else:
            self._bids[price].add(amount)

    def create_ask(self, amount: float, price: float):
        if price > self._last_price:
            raise ValueError('Ask price < top bid price')

        oid = self._new_order(price, amount)
        if price not in self.ask_prices:
            bisect.insort(self.ask_prices, price)
            self._asks[price] = amount
        else:
            self._asks[price] += amount

    def take_bid(self, amount: float, price: float):
        if price not in self._bids:
            raise ValueError('No existing bid order at requested price')
        else:
            self._bids[price] -= amount
            if self._bids[price] < 0.0001:
                self._bids.pop(price)
                self.bid_prices.remove(price)

    def take_ask(self, amount: float, price: float):
        if price not in self._asks:
            raise ValueError('No existing ask order at requested price')
        else:
            self._asks[price] -= amount
            if self._asks[price] < 0.0001:
                self._asks.pop(price)
                self.ask_prices.remove(price)

    def delete_ask(self, amount: float, price: float):
        NotImplementedError

    def delete_ask(self, amount: float, price: float):
        NotImplementedError

    def take_bid_with_id(self, oid):
        NotImplementedError

    def take_ask_with_id(self, oid):
        NotImplementedError

    def _new_order(self, price, amount):
        self._order_id += 1
        oid = self._order_id
        self._orders[oid] = (amount, price)
        return oid


class Paper:
    """Stub for exchange objects. Only supports market/limit orders.

    When used with the OO backtest interface, it should be passed to the
    Backtest object such that the market price is updated while the strategy
    processeses incoming market information.
    """
    def __init__(self, capital: float):
        self.capital = capital
        self.commission = 0
        self.slippage   = 0

        # Each traded pair will have it's own orderbook
        self._orderbooks = defaultdict(Orderbook)  # type: Dict[str, Orderbook]
        self._last_price = 0
        self._last_time = 0

    def update(self, pair: str, price: float, time=None):
        self._last_time  = time or self._last_time
        self._last_price = price

    def buy(self, pair, amount, price=None):
        if price:
            return self.limitBuy(pair, amount, price)
        else:
            self.marketBuy(pair, amount, price)

    def sell(self, pair, amount, price=None):
        if price:
            return self.limitSell(pair, amount, price)
        else:
            self.marketSell(pair, amount, price)

    def marketBuy(self, pair, amount):
        exec_price = self._last_price * (1 + self.commission) * (1 + self.slippage)
        self.capital -= amount * exec_price

        _LOG.info('Market buy {:7.5} {} ${:.5}', amount, pair.upper(), exec_price)
        _LOG.info('Paid {:.5} commission', self._last_price * self.commission)

    def marketSell(self, pair, amount):
        exec_price = self._last_price * (1 - self.commission) * (1 - self.slippage)
        self.capital += amount * exec_price

        _LOG.info('Market buy {:7.5} {} ${:.5}', amount, pair.upper(), exec_price)
        _LOG.info('Paid {:.5} commission', self._last_price * self.commission)

    def limitBuy(self, pair, amount, price):
        _LOG.info('Limit buy {:7.5} {} ${:.5}', amount, pair.upper(), price)
        _LOG.info('Paid {:.5} commission', _price * self.commission)
        return self._orderbooks[pair].create_bid(amount, price)

    def limitSell(self, pair, amount, price):
        _LOG.info('Limit sell {:7.5} {} ${:.5}', amount, pair.upper(), price)
        _LOG.info('Paid {:.5} commission', _price * self.commission)
        return self._orderbooks[pair].create_ask(amount, price)

    def stopBuy(self, pair, amount):
        NotImplementedError

    def stopSell(self, pair, amount):
        NotImplementedError

    def cancelOrder(self, orderid):
        NotImplementedError

    def _matchOpenOrders(self):
        NotImplementedError

    @source('orderfilled:paper')
    @staticmethod
    def _announce_orderfilled(oid):
        return oid

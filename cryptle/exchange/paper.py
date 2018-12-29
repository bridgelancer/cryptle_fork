"""Stub module for emulating an exchange for papertrading.

The class Orderbook is a container for orders of a single instrument and
provides abstraction to updating an orderbook.

The class Paper is an higher level object that keeps track of available capital,
handles incoming data and so on.

Note:
    Orderbook is treated as library code and Paper is treated as application
    code. That means Orderbook only raises and never log whereas Paper only log
    and never raise.
"""


import bisect
import logging
from collections import defaultdict
from typing import Set, Tuple, List, Dict, Union

from cryptle.event import source, on
from cryptle.orderbook import Orderbook
from .exception import ExchangeError, OrderError


# Module logger
logger = logging.getLogger(__name__)


# Type alias for compound return type in orderbook
# (filled ids, (partial filled id, partial fill amount), partial fill amount)
FilledOrders = Tuple[Set[int], Union[Tuple[int, float], None]]


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

        # Open orders
        self._bids = {}
        self._asks = {}
        self._bid_ids = defaultdict(set)
        self._ask_ids = defaultdict(set)

    def __repr__(self):
        return '<{}({} bid, {} ask)>'.format(
            self.__class__.__qualname__, len(self._bids), len(self._asks)
        )

    @property
    def top_bid(self):
        return self.bid_prices[-1]

    @property
    def top_ask(self):
        return self.ask_prices[0]

    def create_bid(self, amount: float, price: float):
        try:
            if price > self.top_ask:
                raise ValueError('Bid price > top ask price')
        except IndexError:
            pass

        if price not in self._bid_ids:
            bisect.insort(self.bid_prices, price)

        oid = self._new_bid(amount, price)
        self._bid_ids[price].add(oid)
        return oid

    def create_ask(self, amount: float, price: float):
        try:
            if price < self.top_bid:
                raise ValueError('Ask price < top bid price')
        except IndexError:
            pass

        if price not in self._ask_ids:
            bisect.insort(self.ask_prices, price)

        oid = self._new_ask(amount, price)
        self._ask_ids[price].add(oid)
        return oid

    def fill_bid(self, amount: float, price: float) -> FilledOrders:
        """Fill the bid orderbook based on a market sell event."""

        filled_orders = set()
        partial = None
        for bid_price in self.bid_prices[::-1]:
            if price > bid_price:
                break
            bids = self._subset_bids(self._bid_ids[bid_price])
            fillable, partial, remainder = self._fillable_orders(bids, amount)
            filled_orders.update(fillable)
            if remainder == 0:
                break
            amount = remainder
        for oid in filled_orders:
            self.delete_bid(oid)
        if partial:
            oid, amount = partial
            _, price = self._bids[oid]
            self._bids[oid] = (amount, price)

        return filled_orders, partial

    def fill_ask(self, amount: float, price: float) -> FilledOrders:
        """Fill the ask orderbook based on a market buy event."""

        filled_orders = set()
        partial = None
        for ask_price in self.ask_prices:
            if price < ask_price:
                break
            asks = self._subset_asks(self._ask_ids[ask_price])
            fillable, partial, remainder = self._fillable_orders(asks, amount)
            filled_orders.update(fillable)
            if remainder == 0:
                break
        for oid in filled_orders:
            self.delete_ask(oid)
        if partial:
            oid, amount = partial
            _, price = self._bids[oid]
            self._bids[oid] = (amount, price)
        return filled_orders, partial

    def fill_bid_by_price(self, price: float) -> FilledOrders:
        """Fill the top bid orders up to provided price."""
        raise NotImplementedError

    def fill_ask_by_price(self, price: float) -> FilledOrders:
        """Fill the top ask orders up to provided price."""
        raise NotImplementedError

    def fill_bid_by_amount(self, amount: float) -> FilledOrders:
        """Fill the top bid orders up to provided amount."""

        filled_orders = set()
        partial = None
        for price in self.bid_prices[::-1]:
            bids = self._subset_bids(self._bid_ids[price])
            fillable, partial, remainder = self._fillable_orders(bids, amount)
            filled_orders.update(fillable)
            if remainder == 0:
                break

        # clean up filled orders
        for oid in filled_orders:
            self.delete_bid(oid)

        # update partially filled order
        if partial:
            oid, amount = partial
            _, price = self._bids[oid]
            self._bids[oid] = (amount, price)
        return filled_orders, partial

    def fill_ask_by_amount(self, amount: float) -> FilledOrders:
        """Fill the top ask orders up to provided amount."""

        filled_orders = set()
        partial = None
        for price in self.ask_prices:
            asks = self._subset_asks(self._ask_ids[price])
            fillable, partial, remainder = self._fillable_orders(asks, amount)
            filled_orders.update(fillable)
            if remainder == 0:
                break

        # clean up filled orders
        for oid in filled_orders:
            self.delete_ask(oid)

        # update partially filled order
        if partial:
            oid, amount = partial
            _, price = self._asks[oid]
            self._asks[oid] = (amount, price)
        return filled_orders, partial

    def delete_bid(self, oid):
        if oid not in self._bids:
            raise ValueError('No bid order of ID {}'.format(oid))

        # get order price
        _, price = self._bids[oid]
        self._bid_ids[price].remove(oid)

        # if this was the last order at it's price, remove empty set in self._bid_ids
        if len(self._bid_ids[price]) == 0:
            self.bid_prices.remove(price)
            del self._bid_ids[price]

        # finally reomve the order
        del self._bids[oid]

    def delete_ask(self, oid):
        if oid not in self._asks:
            raise ValueError('No ask order of ID {}'.format(oid))

        # get order price
        _, price = self._asks[oid]
        self._ask_ids[price].remove(oid)

        # if this was the last order at it's price, remove empty set in self._ask_ids
        if len(self._ask_ids[price]) == 0:
            self.ask_prices.remove(price)
            del self._ask_ids[price]

        # finally reomve the order
        del self._asks[oid]

    def _new_bid(self, amount, price):
        self._order_id += 1
        self._bids[self._order_id] = (amount, price)
        return self._order_id

    def _new_ask(self, amount, price):
        self._order_id += 1
        self._asks[self._order_id] = (amount, price)
        return self._order_id

    def _subset_bids(self, ids):
        return {k: self._bids[k] for k in ids}

    def _subset_asks(self, ids):
        return {k: self._asks[k] for k in ids}

    @staticmethod
    def _fillable_orders(
        orders: Dict[int, Tuple[float, float]], amount: float
    ) -> Tuple[Set[int], Union[Tuple[int, float], None], float]:
        """Find orders to be filled given available amount."""
        filled_orders = set()
        partial = None

        for oid, (order_amount, _) in orders.items():
            if amount >= order_amount:
                filled_orders.add(oid)
            elif amount == 0:
                break
            else:
                partial = (oid, amount)
                amount = 0
                break
            amount -= order_amount
        return filled_orders, partial, amount


def encode_pair(asset, base):
    return asset + base


class Paper:
    """Stub for exchange objects. Supports market/limit orders.

    When used with the OO backtest interface, it should be passed to the
    Backtest object such that the market price is updated while the strategy
    processeses incoming market information.

    Attributes
    ----------
    capital : float
        Amount of cash deposit in the stub exchange account
    commission : float
        Commission for each order transaction
    slippage : float
        Slippage for each order transaction

    """

    def __init__(self, capital: float, commission=0, slippage=0):
        self.capital = capital
        self.commission = 0
        self.slippage = 0

        # Each traded pair will have it's own orderbook
        self._orderbooks = defaultdict(Orderbook)  # type: Dict[str, Orderbook]
        self._last_price = defaultdict(float)  # type: Dict[str, float]

    def __repr__(self):
        return "<{}(capital={})>".format(self.__class__.__qualname__, self.capital)

    def update(self, pair: str, amount: float, price: float, time=None) -> FilledOrders:
        """Update the orderbook based on the provided new trade.

        Args
        ----
        pair : str
            Identifer for the updated traded pair.
        amount : float
            Amount of last trade of updated pair.
        pair : float
            Price of last trade of updated pair.

        Todo
        -----
        Optionally enable market buy/sell to clear this part

        """
        # Accept order type (buy, sell) as a parameter.
        self._last_price[pair] = price
        book = self._orderbooks[pair]

        if len(book.bid_prices) > 0 and price <= book.top_bid:
            filled_ids, partial = book.fill_bid(amount, price)
        elif len(book.ask_prices) > 0 and price >= book.top_ask:
            filled_ids, partial = book.fill_ask(amount, price)

        try:
            for oid in filled_ids:
                self._announce_orderfilled(oid)
            if partial:
                self._announce_orderpartail(*partial)
            return filled_ids, partial
        except NameError:  # no filled orders were found, skip
            pass

    def updatePrice(self, pair: str, price: float):
        """Update the latest reference price without affecting the orderbook."""
        self._last_price[pair] = price

    def buy(self, asset, base, amount, price=None):
        """Automatically decides whether to use market or limit order."""
        if price:
            return self.limitBuy(asset, base, amount, price)
        else:
            self.marketBuy(asset, base, amount)

    def sell(self, asset, base, amount, price=None):
        """Automatically decides whether to use market or limit order."""
        if price:
            return self.limitSell(asset, base, amount, price)
        else:
            self.marketSell(asset, base, amount)

    def marketBuy(self, asset, base, amount) -> Tuple[bool, float]:
        pair = encode_pair(asset, base)
        last_price = self._last_price[pair]
        exec_price = last_price * (1 + self.commission) * (1 + self.slippage)
        self.capital -= amount * exec_price

        logger.info('Market buy {:7.5} {} ${:.5}', amount, pair.upper(), exec_price)
        logger.info('Paid {:.5} commission', last_price * self.commission)

        # Order placement always succeeds
        return True, last_price

    def marketSell(self, asset, base, amount) -> Tuple[bool, float]:
        pair = encode_pair(asset, base)
        last_price = self._last_price[pair]

        exec_price = last_price * (1 - self.commission) * (1 - self.slippage)
        self.capital += amount * exec_price

        logger.info('Market sell {:7.5} {} ${:.5}', amount, pair.upper(), exec_price)
        logger.info('Paid {:.5} commission', last_price * self.commission)

        # Order placement always succeeds
        return True, last_price

    def limitBuy(self, asset, base, amount, price) -> Tuple[bool, int]:
        pair = encode_pair(asset, base)
        last_price = self._last_price[pair]

        exec_price = last_price * (1 + self.commission)
        self.capital -= amount * exec_price

        logger.info('Limit buy {:7.5} {} ${:.5}', amount, pair.upper(), price)
        logger.info('Paid {:.5} commission', price * self.commission)

        # Order placement always succeeds
        return True, self._orderbooks[pair].create_bid(amount, price)

    def limitSell(self, asset, base, amount, price) -> Tuple[bool, int]:
        pair = encode_pair(asset, base)
        last_price = self._last_price[pair]

        exec_price = last_price * (1 - self.commission)
        self.capital += amount * exec_price
        pair = encode_pair(asset, base)

        logger.info('Limit sell {:7.5} {} ${:.5}', amount, pair.upper(), price)
        logger.info('Paid {:.5} commission', price * self.commission)

        # Order placement always succeeds
        return True, self._orderbooks[pair].create_ask(amount, price)

    def cancelOrder(self, orderid):
        NotImplementedError

    @source('order:partialfill:paper')
    def _announce_orderpartail(self, oid, amount):
        return (oid, amount)

    @source('order:fill:paper')
    def _announce_orderfilled(self, oid):
        return oid

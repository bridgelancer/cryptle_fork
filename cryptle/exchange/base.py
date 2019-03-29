"""Standard classes of the exchange module"""

import bisect
import logging

from typing import Set, Tuple, List, Dict, Union
from collections import namedtuple
from collections import defaultdict


# Order is not part of the exports in the exchange public API
# It is mainly used as an immutable result from queries for order status.
Order = namedtuple(
    "Order",
    [
        "oid",
        "amount",
        "limit_price",
        "partial_filled",
        "filled",
        "cancelled",
        "filled_amount",
    ],
)
Order.__doc__ = """
Immutable object representing the state of an open limit order.

Attributes
----------
oid : int
    Order ID. An ID of 0 is reserved to represent a null order.
filled : bool
    Whether the order has been fully filled.
partial_filled : bool
    Whether the order has been partial filled. Only one of either this or
    :attr:`filled` can be true.
cancelled : bool
    Whether the order has been cancelled. Before being filled. Only one of either this
    or :attr:`filled` can be true.

body : dict
    # Todo(pine): naming

filled_amount : float
    The total amount of order that has been filled.
amount : float
    Amount being ordered.
price : float
    Price of the order.
"""


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

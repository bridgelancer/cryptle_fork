import bisect
import logging
from collections import defaultdict
from typing import Set, Tuple, List, Dict

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

    def __repr__(self):
        return '<{}({} bids, {} asks)>'.format(
            self.__qualname__,
            len(self._bids),
            len(self._asks),
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

        if price not in self._bids:
            bisect.insort(self.bid_prices, price)

        oid = self._new_order(amount, price)
        self._bids[price].add(oid)
        return oid

    def create_ask(self, amount: float, price: float):
        try:
            if price < self.top_bid:
                raise ValueError('Ask price < top bid price')
        except IndexError:
            pass

        if price not in self._asks:
            bisect.insort(self.ask_prices, price)

        oid = self._new_order(amount, price)
        self._asks[price].add(oid)
        return oid

    def take_bid(self, amount: float) -> Tuple[Set[int], Tuple[int, float]]:
        filled_orders = set()
        filled_amount = 0
        break_flag = False
        partial_id = partial_filled = None

        # fill bids from highest to lowest price
        for price in self.bid_prices[::-1]:
            for oid in self._bids[price]:
                order_amount, _ = self._open_orders[oid]
                reminding_amount = amount - filled_amount

                if reminding_amount == 0:
                    break_flag = True
                    break
                elif reminding_amount >= order_amount:
                    filled_amount += order_amount
                    filled_orders.add(oid)
                else:
                    # filled all available orders
                    partial_id = oid
                    partial_filled = amount - filled_amount
                    break_flag = True
                    break
            if break_flag:
                break

        # clean up filled orders
        for oid in filled_orders:
            self.delete_bid(oid)

        # mark partially filled order
        self._open_orders[partial_id] = (partial_filled, price)

        return filled_orders, (partial_id, partial_filled)

    def take_ask(self, amount: float):
        filled_orders = set()
        filled_amount = 0
        break_flag = False
        partial_id = partial_filled = None

        # fill asks from highest to lowest price
        for price in self.ask_prices[::-1]:
            for oid in self._asks[price]:
                order_amount, _ = self._open_orders[oid]
                reminding_amount = amount - filled_amount

                if reminding_amount == 0:
                    break_flag = True
                    break
                elif reminding_amount >= order_amount:
                    filled_amount += order_amount
                    filled_orders.add(oid)
                else:
                    # filled all available orders
                    partial_id = oid
                    partial_filled = amount - filled_amount
                    break_flag = True
                    break
            if break_flag:
                break

        # clean up filled orders
        for oid in filled_orders:
            self.delete_ask(oid)

        # mark partially filled order
        self._open_orders[partial_id] = (partial_filled, price)

        return filled_orders, (partial_id, partial_filled)

    def delete_bid(self, oid):
        if oid not in self._open_orders:
            raise ValueError('No bid order of ID {}'.format(oid))

        # get order price
        _, price = self._open_orders[oid]
        self._bids[price].remove(oid)

        # if this was the last order at it's price, remove empty set in self._bids
        if len(self._bids[price]) == 0:
            self.bid_prices.remove(price)
            del self._bids[price]

        # finally reomve the order
        del self._open_orders[oid]

    def delete_ask(self, oid):
        if oid not in self._open_orders:
            raise ValueError('No ask order of ID {}'.format(oid))

        # get order price
        _, price = self._open_orders[oid]
        self._asks[price].remove(oid)

        # if this was the last order at it's price, remove empty set in self._asks
        if len(self._asks[price]) == 0:
            self.ask_prices.remove(price)
            del self._asks[price]

        # finally reomve the order
        del self._open_orders[oid]

    def _new_order(self, amount, price):
        self._order_id += 1
        self._open_orders[self._order_id] = (amount, price)
        return self._order_id


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
        exec_price = self._last_price * (1 + self.commission)
        self.capital -= amount * exec_price

        _LOG.info('Limit buy {:7.5} {} ${:.5}', amount, pair.upper(), price)
        _LOG.info('Paid {:.5} commission', _price * self.commission)
        return self._orderbooks[pair].create_bid(amount, price)

    def limitSell(self, pair, amount, price):
        exec_price = self._last_price * (1 - self.commission)
        self.capital += amount * exec_price

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

    @source('order:partialfill:paper')
    @staticmethod
    def _announce_orderpartail(oid):
        return (oid, amount)

    @source('order:fill:paper')
    @staticmethod
    def _announce_orderfilled(oid):
        return oid

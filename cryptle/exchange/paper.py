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

import cryptle.logging as logging
from collections import defaultdict
from typing import Tuple

from cryptle.event import source, on
from .base import Orderbook, FilledOrders
from .exception import ExchangeError, OrderError


# Module logger
logger = logging.getLogger(__name__)


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

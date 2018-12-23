"""Strategy base classes and related core componets."""

import logging
from collections import defaultdict


logger = logging.getLogger(__name__)


class Portfolio:
    """A Portfolio object is a container and manager of assets.

    Portfolio provides utilities for managing and computing meta information for
    a basket of assets. Common operations which affects the basket state such as
    buy or sell have corresponding methods in the portfolio class.

    Args
    ----
    cash : float, optional
        The amount of cash in the portfolio. Overwrites the base currency's
        amount in the balance if this argument is provided.
    balance : dict, optional
        A dictionary with the portfolio balance amount of each asset.
    base_currency : str, optional
        The currency that denominates the portfolio balance. Defaults to 'usd'.
    shortable : bool, optional
        If short selling is enabled. Defaults to True.

    """

    def __init__(self, cash=None, balance=None, base_currency='usd', shortable=True):

        # Init the internal representation of portfolio balance
        self.balance = defaultdict(float)

        if balance:
            self.balance.update(balance)

        # Set the amount of base currency in the balance, defaults to 0.0
        self.balance[base_currency] = cash or self.balance[base_currency]

        self.base_currency = base_currency  # type:float

        self.shortable = shortable  # type:bool

    def __repr__(self):
        return '<{}({})>'.format(self.__class__.__name__, dict(self.balance))

    @classmethod
    def from_cash(cls, cash, base_currency='usd'):
        """Alternative constructor."""
        return cls(balance={base_currency: cash}, base_currency=base_currency)

    @classmethod
    def from_balance(cls, balance, base_currency='usd'):
        """Alternative constructor."""
        if base_currency not in balance:
            raise ValueError('No entry with base_currency in balance.')
        return cls(balance=balance, base_currency=base_currency)

    def deposit(self, asset: str, amount: float):
        """Increase the amount held of an asset from the balance."""
        self.balance[asset] += amount
        logger.debug('Deposited {} {}', amount, asset)

    def withdraw(self, asset: str, amount: float):
        """Decrease the amount held of an asset from the balance."""
        if asset not in self.balance and not self.shortable:
            raise ValueError('Asset not found in the portfolio')

        if self.balance[asset] < amount and not self.shortable:
            raise ValueError('Insufficient balance of %s' % asset)

        self.balance[asset] -= amount
        logger.debug('Withdrew {} {}', amount, asset)

        # Keep the internal balance free from 0 valued keys
        if self.balance[asset] == 0:
            self.clear(asset)

    def clear(self, asset=None) -> None:
        """Clear the portfolio of an asset. When no asset is provided, clear the whole portfolio
        leaving only the base currency."""
        if not asset:
            cash = self.balance[self.base_currency]
            self.balance = defaultdict(float)
            self.balance[self.base_currency] = cash
        else:
            del self.balance[asset]

    def bought(self, asset: str, amount: float, price: float) -> None:
        """Helper method to update a portfolio after buying an asset.

        Args
        ----
        asset:
            Asset that was bought.
        amount:
            Amount of asset that was bought.
        price:
            Final execution price of the trade.

        """
        self.deposit(asset, amount)
        self.cash -= price * amount

    def sold(self, asset: str, amount: float, price: float) -> None:
        """Helper method to update a portfolio after selling an asset.

        Args
        ----
        asset:
            Asset that was sold.
        amount:
            Amount of asset that was sold.
        price:
            Final execution price of the trade.

        """
        self.withdraw(asset, amount)
        self.cash += price * amount

    def equity(self, asset_prices: dict) -> float:
        """Calculate the current market value of this portfolio.

        Args
        ----
        asset_prices:
            Reference prices of each asset for calculating the total portfolio value. The
            asset_prices is assumed to be be denominated in the portfolio base currency.

        """
        equity = 0.0
        equity += self.balance[self.base_currency]
        for asset, amount in filter(
            lambda x: x[0] != self.base_currency, self.balance.items()
        ):
            equity += amount * (asset_prices[asset] or 0)
        return equity

    @property
    def cash(self):
        return self.balance[self.base_currency]

    @cash.setter
    def cash(self, value: float):
        self.balance[self.base_currency] = value


class Strategy:
    """Abstract base class of all strategies.

    All strategy implementations should inherit from :class:`~cryptle.strategy.Strategy`. This base
    class provide common configurations and utilities for strategies.

    Market data (or any data for that matter) can be pushed to a strategy through dedicated methods
    for each individual type of market data. The supported interfaces are the following methods:

    - :meth:`pushTrade`
    - :meth:`pushCandle`

    The input interface is decoupled from the callback interface. Each of the above methods have a
    corresponding virtual method, with *push* replaced by *on*, such as:

    - :meth:`onTrade`
    - :meth:`onCandle`

    Concrete implementations of :class:`Strategy` must implement at least one of the above methods
    in order to actually perform any reaction to the market.

    .. py:method:: onTrade(pair, price, timestamp, volumn, action)

        This callback handles trade data in the form of price and timestamp.
        on whether this trade was a buy or sell.

        :param str pair: A str code traded pair
        :param float price: Traded price
        :param int timestamp: UNIX timestamp
        :param float volumn: Traded amount
        :param bool action: 0 (buy), 1 (sell)

    .. py:method:: onCandle(pair, open, close, high, low, timestamp, volumn)

        This callback handles candlestick data.

        :param str pair: A str code traded pair
        :param float open: Open price
        :param float high: High price
        :param float low: Low price
        :param float close: Close price
        :param float open: Open price
        :param int timestamp: UNIX timestamp
        :param float volumn: Total traded amount

    Attributes
    ----------
    portfolio : :class:`Portfolio`
        A portfolio object that a strategy instance owns and manges.

    """

    def __init__(self):
        self.portfolio = Portfolio()

    @property
    def base(self):
        return self.portfolio.base_currency

    # [ Data input interface ]
    def pushTrade(self, pair, price, timestamp, volume, action):
        """Input tick data."""
        logger.tick('Received tick of {}', pair)

        try:
            self.onTrade(pair, price, timestamp, volume, action)
        except AttributeError:
            raise AttributeError('Expected implementation of onTrade()')

    def pushCandle(self, pair, op, cl, hi, lo, ts, vol):
        """Input candlestick data."""
        logger.tick('Received candle of {}', pair)

        try:
            self.onCandle(pair, op, cl, hi, lo, ts, vol)
        except AttributeError:
            raise AttributeError('Expected implementation of onCandle()')

    # [ Helpers to access portfolio object ]
    @property
    def hasCash(self):
        """Return a boolean on whether the strategy has available cash."""
        return self.portfolio.cash > 0


class ExchangeError(Exception):
    pass


class TradingStrategy(Strategy):
    """Base class for strategies that will directly place orders at exchanges.

    Args
    ----
    exchange : :class:`~cryptle.exchange.Exchange`
        The exchange that will be used to place orders from the strategy.

    Attributes
    ----------
    exchange : :class:`~cryptle.exchange.Exchange`
        The exchange that will be used to place orders from the strategy.
    equity_at_risk : float
        Maximum fraction of total captial that can be used in any 1 trade.

    """

    def __init__(self, exchange):
        Strategy.__init__(self)
        self.exchange = exchange
        self.equity_at_risk = 0.1

    # [ Helpers to access exchange ]
    def marketBuy(self, asset: str, amount: float) -> float:
        """Send market buy request to associated exchange"""
        if amount <= 0:
            raise ValueError("Expect positive value for amount.")

        logger.debug('Placing market buy for {:.6g} {}', amount, asset)
        success, price = self.exchange.marketBuy(asset, self.base, amount)

        if success:
            self._cleanupBuy(asset, price, amount)
            return price
        else:
            raise ExchangeError('Order placement failed')

    def marketSell(self, asset: str, amount: float) -> float:
        """Send market sell request to associated exchange"""
        if amount < 0:
            raise ValueError("Expect positive value for amount.")

        logger.debug('Placing market sell for {:.6g} {}', amount, asset)
        success, price = self.exchange.marketSell(asset, self.base, amount)

        if success:
            self._cleanupSell(asset, amount, price)
            return price
        else:
            raise ExchangeError('Order placement failed')

    def limitBuy(self, asset: str, amount: float, price: float) -> int:
        """Send limit buy request to associated exchange"""
        if amount < 0:
            raise ValueError("Expect positive value for amount.")
        if price < 0:
            raise ValueError("Expect positive value for price.")

        logger.debug('Placing limit buy for {:.6g} {} @${:.6g}', amount, asset, price)
        success, oid = self.exchange.limitBuy(asset, self.base, amount, price)

        if success:
            return oid
        else:
            raise ExchangeError('Order placement failed')

    def limitSell(self, asset: str, amount: float, price: float) -> int:
        """Send market buy request to associated exchange"""
        if amount < 0:
            raise ValueError("Expect positive value for amount.")
        if price < 0:
            raise ValueError("Expect positive value for price.")

        logger.debug('Placing limit sell for {:.6g} {} @${:.6g}', amount, asset, price)
        success, oid = self.exchange.limitSell(asset, self.base, amount, price)

        if success:
            return oid
        else:
            raise ExchangeError('Order placement failed')

    def _cleanupBuy(self, asset: str, price: float, amount: float) -> None:
        self.portfolio.bought(asset, amount, price)
        logger.info('Bought {:7.6g} {} @${:<7.6g}', amount, asset, price)

    def _cleanupSell(self, asset: str, amount: float, price: float) -> None:
        self.portfolio.sold(asset, amount, price)
        logger.info('Sold   {:7.6g} {} @${:<7.6g}', amount, asset, price)


class SingleAssetStrategy(TradingStrategy):
    """A strategy that only trades a single asset against the base currency.

    Overrides the buy sell methods to supply the same asset as argument
    everytime in all buy/sell methods.

    Args
    ----
    exchange : :class:`~cryptle.exchange.Exchange`
        The exchange that will be used to place orders from the strategy.
    asset : str
        The traded asset.

    Attributes
    ----------
    asset : str
        The traded asset of this strategy
    equity_at_risk : float
        Maximum amount of equity that can be used in a single trade.

    Note
    ----
    When given a portfolio, Strategy(Base) assumes that it is the only strategy
    trading on that portfolio for the given pair.

    """

    def __init__(self, exchange, asset):
        TradingStrategy.__init__(self, exchange)
        self.asset = asset

    def pushTrade(
        self, price: float, timestamp: float, volume: float, action: bool
    ) -> None:

        # todo: input validation
        try:
            self.onTrade(price, timestamp, volume, action)
        except AttributeError:
            raise AttributeError('Expected implementation of onTrade()')

    def pushCandle(
        self, op: float, cl: float, hi: float, lo: float, ts: int, vol: float
    ) -> None:

        # todo: input validation
        try:
            self.onCandle(op, cl, hi, lo, ts, vol)
        except AttributeError:
            raise AttributeError('Expected implementation of onCandle()')

    def marketBuy(self, amount: float) -> float:
        """Wrapper over the parent's `marketBuy()` for single asset.

        Args
        ----
        amount: Amount to sell.

        """
        return super().marketBuy(self.asset, amount)

    def marketSell(self, amount: float) -> float:
        """Wrapper over the base parent's `marketSell()` for single asset.

        Args
        ----
        amount: Amount to sell.

        """
        return super().marketSell(self.asset, amount)

    def limitBuy(self, amount: float, price: float):
        """Wrapper over the base parent's `limitBuy()` for single asset.

        Args
        ----
        amount: Amount to buy.
        price: Buy price.

        """
        super().limitBuy(self.asset, amount, price)

    def limitSell(self, amount: float, price: float):
        """Wrapper over the base parent's `limitSell()` for single asset.

        Args
        ----
        amount: Amount to sell.
        price: Sell price.

        """
        super().limitSell(self.asset, amount, price)

    def maxBuyAmount(self, price: float) -> float:
        """Return the maximum amount of asset that the portfolio can afford
        given the current price.

        Args
        ----
        price:
            Current price of the asset to be bought.

        """
        equity = self.portfolio.equity({self.asset: price})
        max_equi = self.equity_at_risk * equity / price
        max_cash = self.portfolio.cash / price
        return min(max_equi, max_cash)

    def maxSellAmount(self):
        """Return the maximum amount of asset that the portfolio can sell.

        Args
        ----
        price:
            Current price of the asset to be sold.

        """
        return self.portfolio.balance[self.asset]

    @property
    def hasBalance(self) -> bool:
        """Returns a boolean on whether the strategy is holding any asset."""
        try:
            return self.portfolio.balance[self.asset] == 0
        except:
            return False


from cryptle.event import on, source


class EventMarketDataMixin:
    @on('candle')
    def pushCandle(self, data):
        """Override strategy input interfaces for plugging into an event bus."""
        pair, op, cl, hi, lo, ts, vol = data
        super().pushCandle(pair, op, cl, hi, lo, ts, vol)

    @on('trade')
    def pushTrade(self, data):
        """Override strategy input interfaces for plugging into an event bus."""
        pair, price, timestamp, volume, action = data
        super().pushTrade(pair, price, timestamp, volume, action)


class EventOrderMixin:
    @source('order:marketbuy')
    def marketBuy(self, asset: str, amount: float):
        """
        Override base class's :any:`marketBuy` to raise event
        ``order:marketbuy`` instead of placing order with exchange directly.

        :rtype: (str, float)

        """
        return asset, amount

    @source('order:marketsell')
    def marketSell(self, asset: str, amount: float):
        """
        Override base class's :any:`marketSell` to raise event
        ``order:marketsell`` instead of placing order with exchange directly.

        :rtype: (str, float)

        """
        return asset, amount

    @source('order:limitbuy')
    def limitBuy(self, asset: str, amount: float, price: float):
        """
        Override base class's :any:`limitBuy` to raise event
        ``order:limitbuy`` instead of placing order with exchange directly.

        :rtype: (str, float, float)

        """
        return asset, amount, price

    @source('order:limitsell')
    def limitSell(self, asset: str, amount: float, price: float):
        """
        Override base class's :any:`limitSell` to raise event
        ``order:limitsell`` instead of placing order with exchange directly.

        :rtype: (str, float, float)

        """
        return asset, amount, price

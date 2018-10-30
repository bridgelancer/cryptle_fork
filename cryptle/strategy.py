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

    """

    def __init__(self, cash=None, balance=None, base_currency='usd'):

        # Init the internal representation of portfolio balance
        self.balance = defaultdict(float)

        if balance:
            self.balance.update(balance)

        # Set the amount of base currency in the balance, defaults to 0.0
        self.balance[base_currency] = cash or self.balance[base_currency]

        self.base_currency = base_currency

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

    def deposit(self, asset, amount):
        """Increase the amount held of an asset from the balance."""
        self.balance[asset] += amount
        logger.debug('Deposited {} {}'.format(amount, asset))

    def withdraw(self, asset, amount):
        """Decrease the amount held of an asset from the balance."""
        if asset not in self.balance:
            raise ValueError('Asset not found in the portfolio')

        if self.balance[asset] < amount:
            raise ValueError('Insufficient balance of %s' % asset)

        self.balance[asset] -= amount
        logger.debug('Withdrew {} {}'.format(amount, asset))

        # Keep the internal balance free from 0 valued keys
        if self.balance[asset] == 0:
            self.clear(asset)

    def clear(self, asset=None):
        """Clear the portfolio of an asset. When no asset is provided, clear the whole portfolio
        leaving only the base currency."""
        if not asset:
            cash = self.balance[self.base_currency]
            self.balance = defaultdict(float)
            self.balance[self.base_currency] = cash
        else:
            del self.balance[asset]

    def bought(self, asset, amount, cost):
        """Helper method to update a portfolio after buying."""
        self.deposit(asset, amount)
        self.cash -= cost

    def sold(self, asset, amount, cost):
        """Helper method to update a portfolio after selling."""
        self.withdraw(asset, amount)
        self.cash += cost

    def equity(self, asset_prices):
        """Calculate the current market value of this portfolio.

        Args
        ----
        asset_prices : dict
            Reference prices of each asset for calculating the total portfolio value. The
            asset_prices is assumed to be be denominated in the portfolio base currency.

        """
        equity = 0.0
        equity += self.balance[self.base_currency]
        for asset, amount in filter(lambda x: x[0] != self.base_currency, self.balance.items()):
            equity += amount * asset_prices[asset]
        return equity

    @property
    def cash(self):
        """float: """
        return self.balance[self.base_currency]

    @cash.setter
    def cash(self, value):
        self.balance[self.base_currency] = value


class Strategy:
    """Abstract base class of strategies.

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

        This callback handles trade data in the form of price and timestamp. *action* is a boolean
        on whether this trade was a buy or sell.

    .. py:method:: onCandle(pair, open, close, high, low, timestamp, volumn)

        This callback handles candlestick data.

    Attribute
    ---------
    portfolio : :class:`Portfolio`
        A portfolio object that a strategy instance owns and manges.
    exchange : :class:`~cryptle.exchange.Exchange`
        The exchange that will be used to place orders from the strategy.
    """

    def __init__(self):
        self.portfolio = Portfolio()
        self.exchange = None

    # [ Data input interface ]
    def pushTrade(self, pair, price, timestamp, volume, action):
        """Input tick data."""
        logger.tick('Received tick of {}', pair)
        self.onTrade(pair, price, timestamp, volume, action)

    def pushCandle(self, pair, op, cl, hi, lo, ts, vol):
        """Input candlestick data."""
        logger.tick('Received candle of {}', pair)
        self.onCandle(pair, op, cl, hi, lo, ts, vol)

    # [ Helpers to access portfolio object ]
    def hasCash(self):
        """Return a boolean on whether the strategy has available cash."""
        return self.portfolio.cash > 0

    # [ Helpers to access exchange ]
    # Todo: fix the function signature for the exchange interface
    def marketBuy(self, asset, amount):
        """Send market buy request to associated exchange"""
        if amount <= 0:
            raise ValueError("Expect positive value for amount.")

        logger.debug('Placing market buy for {:.6g} {}', amount, asset)
        res = self.exchange.marketBuy(asset, amount)
        self._cleanupBuy(asset, res)

    def marketSell(self, asset, amount):
        """Send market sell request to associated exchange"""
        if amount < 0:
            raise ValueError("Expect positive value for amount.")

        logger.debug('Placing market sell for {:.6g} {}', amount, asset)
        res = self.exchange.marketSell(asset, amount)
        self._cleanupSell(asset, res)

    def limitBuy(self, asset, amount, price):
        """Send limit buy request to associated exchange"""
        if amount < 0:
            raise ValueError("Expect positive value for amount.")
        if price  < 0:
            raise ValueError("Expect positive value for price.")

        logger.debug('Placing limit buy for {:.6g} {} @${:.6g}', amount, asset, price)
        res = self.exchange.limitBuy(asset, amount, price)
        self._cleanupBuy(asset, res)

    def limitSell(self, asset, amount, price):
        """Send market buy request to associated exchange"""
        if amount < 0:
            raise ValueError("Expect positive value for amount.")
        if price  < 0:
            raise ValueError("Expect positive value for price.")

        logger.debug('Placing limit sell for {:.6g} {} @${:.6g}', amount, asset, price)
        res = self.exchange.limitSell(asset, amount, price)
        self._cleanupSell(asset, res)

    # Reconcile actions made on the exchange with the portfolio
    def _cleanupBuy(self, asset, res):
        if res['status'] == 'error':
            logger.error('Buy failed {}', asset)
            return

        price = float(res['price'])
        amount = float(res['amount'])
        timestamp = int(res['timestamp'])

        self.portfolio.deposit(asset, amount, price)
        self.portfolio.cash -= amount * price
        # self.trades.append([timestamp, price])

        logger.info(
            'Bought {:7.6g} {} @${:<7.6g} {:s}',
            amount,
            asset,
            price,
            datetime.fromtimestamp(timestamp)
        )

    def _cleanupSell(self, asset, res):
        if res['status'] == 'error':
            logger.error('Sell failed {}', asset)
            return

        price = float(res['price'])
        amount = float(res['amount'])
        timestamp = int(res['timestamp'])

        self.portfolio.withdraw(self.asset, amount)
        self.portfolio.cash += amount * price
        # self.trades[-1] += [timestamp, price]

        logger.info(
            'Sold   {:7.6g} {} @${:<7.6g} {:s}',
            amount,
            asset,
            price,
            datetime.fromtimestamp(timestamp)
        )


class SingleAssetStrat(Strategy):
    """A strategy that only trades a single asset against the base currency.

    Overrides the buy sell methods to supply the same asset as argument
    everytime in all buy/sell methods.

    Args
    ----
    asset: str
        The traded asset.

    Attribute
    ---------
    asset : str
        The traded asset of this strategy
    equity_at_risk : float
        Maximum amount of equity that can be used in a single trade.

    Note
    ----
    When given a portfolio, Strategy(Base) assumes that it is the only strategy
    trading on that portfolio for the given pair.

    """

    def __init__(self, asset):
        super().__init__()
        self.asset = asset
        self.equity_at_risk = 0.1

    # Todo: fix the function signature for the exchange interface
    def marketBuy(self, amount):
        """Wrapper over the base Strategy.marketBuy() for single asset."""
        super().marketBuy(self.asset, amount)

    def marketSell(self, amount):
        """Wrapper over the base Strategy.marketSell() for single asset."""
        super().marketSell(self.asset, amount)

    def limitBuy(self, amount, price):
        """Wrapper over the base Strategy.limitBuy() for single asset."""
        super().limitBuy(self.asset, amount, price)

    def limitSell(self, amount, price):
        """Wrapper over the base Strategy.limitSell() for single asset."""
        super().limitSell(self.asset, amount, price)

    def maxBuyAmount(self, price):
        """Return the maximum amount of asset that the portfolio can afford
        given the current price.

        Args
        ----
        price : float
            Current price of the asset to buy.

        """
        equity = self.portfolio.equity({self.asset[price]})
        max_equi = self.equity_at_risk * equity / price
        max_cash = self.portfolio.cash / price
        return min(max_equi, max_cash)

    def maxSellAmount(self):
        """Return the maximum amount of asset that the portfolio can sell."""
        return self.portfolio.balance[self.asset]

    def hasBalance(self):
        try:
            return self.portfolio.balance[self.asset] > 0
        except:
            return False


from cryptle.event import on, source


class EventMarketDataMixin:
    @on('candle')
    def pushCandle(self, data):
        pair, op, cl, hi, lo, ts, vol = data
        super().pushCandle(pair, op, cl, hi, lo, ts, vol)

    @on('trade')
    def pushTrade(self, data):
        pair, price, timestamp, volume, action = data
        super().pushTrade(pair, price, timestamp, volume, action)


class EventOrderMixin:
    @source('order:marketbuy')
    def marketBuy(self, asset, amount):
        return asset, amount

    @source('order:marketsell')
    def marketSell(self, asset, amount):
        return asset, amount

    @source('order:limitbuy')
    def limitBuy(self, asset, amount, price):
        return asset, amount

    @source('order:limitsell')
    def limitSell(self, asset, amount, price):
        return asset, amount

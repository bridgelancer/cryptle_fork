# @Todo Module level doc

import logging


logger = logging.getLogger(__name__)


class Portfolio:
    '''A Portfolio object is a collection of assets.

    Note:
        The value of balance[base_currency] will be overwritten by cash when
        cash is not None. Only default __init__ allows custom balance_value.

    Attributes:
        base_currency: The base currency that denominates the account balance.
        balance: A dictionary with the portfolio balance values of each asset.
        equity: Net balance value.
    '''

    def __init__(self, cash=None, balance=None, base_currency='usd', balance_value=None):
        if cash is None and balance is None:
            raise ValueError('Both cash and balance were None')

        self.balance = balance or {base_currency: cash}
        self.balance[base_currency] = cash or self.balance[base_currency]
        self.base_currency = base_currency
        self.balance_value = balance_value or {}


    @classmethod
    def from_cash(cls, cash, base_currency='usd'):
        return cls(balance={base_currency: cash}, base_currency=base_currency)


    @classmethod
    def from_balance(cls, balance, base_currency='usd'):
        if base_currency not in balance:
            raise ValueError('No entry with base_currency in balance.')
        return cls(balance=balance, base_currency=base_currency)


    def deposit(self, asset, amount, price=0):
        try:
            self.balance[asset] += amount
            self.balance_value[asset] += amount * price
        except KeyError:
            self.balance[asset] = amount
            self.balance_value = amount * price
        logger.debug('Deposited {} {}'.format(amount, asset))


    def withdraw(self, asset, amount):
        try:
            self.balance_value *= (self.balance[asset] - amount) / self.balance[asset]
            self.balance[asset] -= amount
            logger.debug('Withdrew {} {}'.format(amount, asset))
        except KeyError:
            raise RuntimeWarning('Attempt was made to withdraw from an empty balance')


    @property
    def equity(self):
        return sum(self.balance_value.values()) + self.cash


    @property
    def cash(self):
        return self.balance[self.base_currency]


    @cash.setter
    def cash(self, value):
        self.balance[self.base_currency] = value


    def updateEquity(self, price):
        for asset, amount in filter(lambda x: x[0] != self.base_currency, self.balance.items()):
            try:
                self.balance_value[asset] = amount * price[asset]
            except KeyError:
                pass
        return self.equity



class Strategy:
    '''Base class of strategies.

    To create a new strategy, subclass from :class:`Strategy` and implement at
    least one of the data handling callback methods, and the execute method. The
    callback functions are:

    - :meth:`handleTick`
    - :meth:`handleCandle`
    - :meth:`handleText`

    Metrics/Indicators that needs to be updated tick by tick has to go into the
    indicators dict. The update method will be called on the indicators.

    Args:
        pair: String representation of the trade coin pair (meta info)
        portfolio: Portfolio managed by the strategy instance
        exchange: Exchange to be used by the strategy for order placements
        equity_at_risk: The maximum proportion of equity that will be traded
        print_timestamp: Flag for printing timestamp at buy/sell confirmation

    Note:
        When given a portfolio, Strategy(Base) assumes that it is the only
        strategy trading on that portfolio for the given pair.
    '''

    def __init__(self,
            *,
            asset,
            base_currency,
            portfolio,
            exchange,
            equity_at_risk=1,
            print_timestamp=True):

        self.asset = asset
        self.base_currency = base_currency
        self.portfolio = portfolio
        self.exchange = exchange
        self.equity_at_risk = equity_at_risk
        self.print_timestamp = print_timestamp

        self.trades = []
        if self.indicators:
            for k, v in self.indicators.items():
                self.__dict__[k] = v


    # [Data input interface]
    # Wrappers for trade logical steps
    def pushTick(self, price, timestamp, volume, action):
        '''Public inferface for tick data'''

        self._checkHasExchange()
        logger.tick('Received tick')

        self.last_price = price
        self.last_timestamp = timestamp
        for k, v in self.indicators.items():
            try:
                # @Deprecated
                v.update(price, timestamp, volume, action)
            except:
                v.pushTick(price, timestamp, volume, action)

        if self.handleTick(price, timestamp, volume, action) is None:
            self.execute(timestamp)


    def pushCandle(self, op, cl, hi, lo, ts, vol):
        '''Public inferface for aggregated candlestick'''

        self._checkHasExchange()
        logger.tick('Received candle')

        # @Fix Need to separated tick based and candle based indicators
        self.last_price = cl
        self.last_timestamp = ts
        for k, v in self.indicators.items():
            try:
                # @Deprecated
                v.update(op, cl, hi, lo, ts, vol)
            except:
                v.pushTick(price, timestamp, volume, action)

        if self.handleCandle(op, cl, hi, lo, ts, vol) is None:
            self.execute(ts)


    def handleTick(self):
        '''Process tick data and generate trade signals.'''
        raise NotImplementedError


    def handleCandle(self):
        '''Process candlestick data and generate trade signals.'''
        raise NotImplementedError


    def execute(self):
        '''Execute the trade signals raised by handling new data'''
        raise NotImplementedError


    def pushText(self, string, timestamp):
        '''Stub method as example of future possible data types.'''
        raise NotImplementedError


    def handleText(self, string, timestamp):
        '''Process textmethod as example of future possible data types.'''
        raise NotImplementedError


    # [Portfolio interface]
    # Wrappers of portfolio object, mostly for convenience purpose
    @property
    def hasBalance(self):
        try:
            return self.portfolio.balance[self.asset] > 0
        except:
            return False


    @property
    def hasCash(self):
        return self.portfolio.cash > 0


    @property
    def equity(self):
        return self.portfolio.equity


    @property
    def maxBuyAmount(self):
        max_equi = self.equity_at_risk * self.equity / self.last_price
        max_cash = self.portfolio.cash / self.last_price
        return min(max_equi, max_cash)


    @property
    def maxSellAmount(self):
        return self.portfolio.balance[self.asset]


    # [Exchange interface]
    # Wrappers of exchange object for fine grain control/monitor over buy/sell process
    def marketBuy(self, amount, message=''):
        if amount > 0: raise ValueError("Amount must be larger than zero")
        msg = 'Placing market buy for {:.6g} {} {:s}'
        logger.debug(msg.format(amount, self.asset.upper(), message))
        res = self.exchange.sendMarketBuy(self.asset, amount)
        self._cleanupBuy(res, message)


    def marketSell(self, amount, message=''):
        if amount > 0: raise ValueError("Amount must be larger than zero")
        msg = 'Placing market sell for {:.6g} {} {:s}'
        logger.debug(msg.format(amount, self.asset.upper(), message))
        res = self.exchange.sendMarketSell(self.asset, amount)
        self._cleanupSell(res, message)


    def limitBuy(self, amount, price, message=''):
        if amount > 0: raise ValueError("Amount must be larger than zero")
        if price  > 0: raise ValueError("Price must be larger than zero")
        msg = 'Placing limit buy for {:.6g} {} @${:.6g} {:s}'
        logger.debug(msg.format(amount, self.asset.upper(), price, message))
        res = self.exchange.sendLimitBuy(self.asset, amount, price)
        self._cleanupBuy(res, message)


    def limitSell(self, amount, price, message=''):
        if amount > 0: raise ValueError("Amount must be larger than zero")
        if price  > 0: raise ValueError("Price must be larger than zero")
        msg = 'Placing limit sell for {:.6g} {} @${:.6g} {:s}'
        logger.debug(msg.format(amount, self.asset.upper(), price, message))
        res = self.exchange.sendLimitSell(self.asset, amount, price)
        self._cleanupSell(res, message)


    # Reconcile actions made on the exchange with the portfolio
    def _cleanupBuy(self, res, message=None):
        if res['status'] == 'error':
            logger.error('Buy failed {} {}'.format(self.asset.upper(), message))
            return

        price = float(res['price'])
        amount = float(res['amount'])
        timestamp = int(res['timestamp'])

        self.portfolio.deposit(self.asset, amount, price)
        self.portfolio.cash -= amount * price
        self.trades.append([timestamp, price])

        msg = 'Bought {:7.6g} {} @${:<7.6g} {:s}'
        if self.print_timestamp:
            msg += ' at {:%Y-%m-%d %H:%M:%S}'
        logger.info(msg.format(
                amount,
                self.asset.upper(),
                price,
                message,
                datetime.fromtimestamp(timestamp)))


    def _cleanupSell(self, res, message=None):
        if res['status'] == 'error':
            logger.error('Sell failed {} {}'.format(self.asset.upper(), message))
            return

        price = float(res['price'])
        amount = float(res['amount'])
        timestamp = int(res['timestamp'])

        self.portfolio.withdraw(self.asset, amount)
        self.portfolio.cash += amount * price
        self.trades[-1] += [timestamp, price]

        msg = 'Sold   {:7.6g} {} @${:<7.6g} {:s}'
        if self.print_timestamp:
            msg += ' at {:%Y-%m-%d %H:%M:%S}'
        logger.info(msg.format(
                amount,
                self.asset.upper(),
                price,
                message,
                datetime.fromtimestamp(timestamp)))


    def _checkHasExchange(self):
        if self.exchange is None:
            raise AttributeError('An exchange has to be associated before strategy runs')

from .utility import *
import logging

logger = logging.getLogger('Cryptle')

# @Consider using Enum instead?
class DirectionFlag:
    '''A boolean which can be accessed with specialised named attritubes.

    The value of this flag can be accessed through members, up/down. The value
    of these attributes are always oppositive of each other.
    '''

    def __init__(s):
        s._up = s._down = False

    @property
    def up(s):
        return s._up

    @property
    def down(s):
        return s._down

    @up.setter
    def up(s, value):
        s._up = value
        s._down = not value

    @down.setter
    def down(s, value):
        s._down = value
        s._up = not value


class TradeFlag:
    '''A boolean which can be accessed with specialised named attritubes.

    The value of this flag can be accessed through members, buy/sell. The value
    of these attributes are always oppositive of each other.
    '''

    def __init__(s):
        s._buy = s._sell = False

    @property
    def buy(s):
        return s._buy

    @property
    def sell(s):
        return s._sell

    @buy.setter
    def buy(s, value):
        s._buy = value
        s._sell = not value

    @sell.setter
    def sell(s, value):
        s._sell = value
        s._buy = not value


class Portfolio:
    '''A proxy data structure for keeping track of balance in an account.'''

    def __init__(self, cash, balance=None, balance_value=None):
        checkType(cash, int, float)

        self.cash = cash
        self.balance = balance or {}
        self.balance_value = balance_value or {}


    def deposit(self, pair, amount, price=0):
        checkType(pair, str)
        checkType(amount, int, float)
        checkType(price, int, float)

        try:
            self.balance[pair] += amount
            self.balance_value[pair] += amount * price
        except KeyError:
            self.balance[pair] = amount
            self.balance_value[pair] = amount * price


    def withdraw(self, pair, amount):
        checkType(pair, str)
        checkType(amount, int, float)

        try:
            self.balance_value[pair] *= ((self.balance[pair] - amount) / self.balance[pair])
            self.balance[pair] -= amount
        except (KeyError, ZeroDivisionError):
            raise RuntimeWarning('Attempt was made to withdraw from an empty balance')


    def clear(self, pair):
        checkType(pair, str)
        self.balance[pair] = 0


    def clearAll(self):
        self.balance = {}


    @property
    def equity(self):
        asset = sum(self.balance_value.values())
        return self.cash + asset


class Strategy:
    '''Base class of strategies implementation/realisations.

    Provides wrapper function for buy/sell and portfolio management.

    Realisation classes must define the following functions:
    - generateSignal()
    - execute()

    Metrics/Indicators that needs to be updated tick by tick has to go into the
    indicators dict. The update method will be called on the indicators whenever
    tick() is called
    '''

    def __init__(self, pair=None, portfolio=None, exchange=None, equity_at_risk=1):
        self.pair = pair
        self.portfolio = portfolio or Portfolio(10000)
        self.exchange = exchange
        self.equity_at_risk = equity_at_risk

        for k, v in self.indicators.items():
            self.__dict__[k] = v

        self.trades = []


    # [Data input interface]
    # Wrappers for trade logical steps
    def tick(self, price, timestamp, volume, action, callback=None):
        if self.exchange is None:
            raise TypeError('An exchange has to be associated before strategy runs')

        for k, v in self.indicators.items():
            v.update(price, timestamp, volume, action)

        self.last_price = price
        self.timestamp = timestamp
        if self.generateSignal(price, timestamp, volume, action) is None:
            self.execute(timestamp)

        if callback:
            callback(self)


    def news(self, string, timestamp):
        raise NotImplementedError


    def tweet(self, string, timestamp):
        raise NotImplementedError


    # [Portfolio interface]
    # Wrappers of portfolio object, mostly for convenience purpose
    @property
    def hasBalance(self):
        try:
            return self.portfolio.balance[self.pair] > 0
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
        return self.portfolio.balance[self.pair]


    # [Exchange interface]
    # Wrappers of exchange object for fine grain control/monitor over buy/sell process
    def marketBuy(self, amount, message='', timestamp=None):
        checkType(amount, int, float)
        checkType(message, str)
        assert amount > 0

        logger.debug('Placing market buy for {:.6g} {} {:s}'.format(amount, self.pair.upper(), message))
        res = self.exchange.marketBuy(self.pair, amount)

        self._cleanupBuy(res, message)


    def marketSell(self, amount, message='', timestamp=None):
        checkType(amount, int, float)
        checkType(message, str)
        assert amount > 0

        logger.debug('Placing market sell for {:.6g} {} {:s}'.format(amount, self.pair.upper(), message))
        res = self.exchange.marketSell(self.pair, amount)

        self._cleanupSell(res, message)


    def limitBuy(self, amount, price, message='', timestamp=None):
        checkType(amount, int, float)
        checkType(price, int, float)
        checkType(message, str)
        assert amount > 0
        assert price > 0

        logger.debug('Placing limit buy for {:.6g} {} @${:.6g} {:s}'.format(amount, self.pair.upper(), price, message))
        res = self.exchange.limitBuy(self.pair, amount, price)

        self._cleanupBuy(res, message)


    def limitSell(self, amount, price, message='', timestamp=None):
        checkType(amount, int, float)
        checkType(price, int, float)
        checkType(message, str)
        assert amount > 0
        assert price > 0

        logger.debug('Placing limit sell for {:.6g} {} @${:.6g} {:s}'.format(amount, self.pair.upper(), price, message))
        res = self.exchange.limitSell(self.pair, amount, price)

        self._cleanupSell(res, message)


    # Reconcile actions made on the exchange with the portfolio
    def _cleanupBuy(self, res, message=None, pair=None):
        if res['status'] == 'error':
            logger.error('Buy failed {} {}'.format(self.pair.upper(), message))
            return

        price = float(res['price'])
        amount = float(res['amount'])
        timestamp = int(res['timestamp'])

        self.portfolio.deposit(self.pair, amount, price)
        self.portfolio.cash -= amount * price
        self.trades.append([timestamp, price])

        logger.info('Bought {:.7g} {} @${:<.6g} {}'.format(amount, self.pair.upper(), price, message))


    def _cleanupSell(self, res, message=None):
        if res['status'] == 'error':
            logger.error('Sell failed {} {}'.format(self.pair.upper(), message))
            return

        price = float(res['price'])
        amount = float(res['amount'])
        timestamp = int(res['timestamp'])

        self.portfolio.withdraw(self.pair, amount)
        self.portfolio.cash += amount * price
        self.trades[-1] += [timestamp, price]

        logger.info('Sold   {:.7g} {} @${:<.6g} {}'.format(amount, self.pair.upper(), price, message))


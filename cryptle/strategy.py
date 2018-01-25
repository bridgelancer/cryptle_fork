from _utility import *
from exchange import *

logger = logging.getLogger('Cryptle')

class Portfolio:

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


    def getEquity(self):
        asset = sum(self.balance_value.values())
        return self.cash + asset


class Strategy:
# Base class of any new strategy, provides wrapper function for buy/sell and portfolio management
# Realisation classes must define the following functions:
# - generateSignal()
# - execute()

    def __init__(self, pair, portfolio=None, equity_at_risk=1, exchange=None):
        self.pair = pair
        self.equity_at_risk = equity_at_risk
        self.portfolio = portfolio or Portfolio(10000)
        self.exchange = exchange or PaperExchange()

        for k, v in self.indicators.items():
            self.__dict__[k] = v

        self.trades = []


    def hasBalance(self, pair=None):
        pair = pair or self.pair

        try:
            return self.portfolio.balance[self.pair] > 0
        except:
            return False


    def hasCash(self):
        return self.portfolio.cash > 0


    def getEquity(self):
        return self.portfolio.getEquity()


    def maxBuyAmount(self, price, pair=None):
        pair = pair or self.pair
        return min(self.equity_at_risk * self.getEquity() / price, self.portfolio.cash / price)


    def maxSellAmount(self, pair=None):
        pair = pair or self.pair
        return self.portfolio.balance[self.pair]

    # Recieve and process tick data
    def tick(self, tick):
        price, volume, timestamp = unpackTick(tick)
        for k, v in self.indicators.items():
            v.update(tick)

        self.generateSignal(self, price=price, volume=volume, timestamp=timestamp)
        self.execute()

    # Recieve and process news data
    def news(self, string):
        raise NotImplementedError

    # Recieve and process tweet data
    def tweet(self, string):
        raise NotImplementedError


    def marketBuy(self, amount, message='', timestamp=None):
        checkType(amount, int, float)
        checkType(message, str)
        assert amount > 0

        logger.debug('Placing market buy for {:.6g} {} {:s}'.format(amount, self.pair.upper(), message))
        res = self.exchange.marketBuy(self.pair, amount)

        self._cleanupBuy(res, message, timestamp)


    def marketSell(self, amount, message='', timestamp=None):
        checkType(amount, int, float)
        checkType(message, str)
        assert amount > 0

        logger.debug('Placing market sell for {:.6g} {} {:s}'.format(amount, self.pair.upper(), message))
        res = self.exchange.marketSell(self.pair, amount)

        self._cleanupSell(res, message, timestamp)


    def limitBuy(self, amount, price, message='', timestamp=None):
        checkType(amount, int, float)
        checkType(price, int, float)
        checkType(message, str)
        assert amount > 0
        assert price > 0

        logger.debug('Placing limit buy for {:.6g} {} @${:.6g} {:s}'.format(amount, self.pair.upper(), price, message))
        res = self.exchange.limitBuy(self.pair, amount, price)

        self._cleanupBuy(res, message, timestamp)


    def limitSell(self, amount, price, message='', timestamp=None):
        checkType(amount, int, float)
        checkType(price, int, float)
        checkType(message, str)
        assert amount > 0
        assert price > 0

        logger.debug('Placing limit sell for {:.6g} {} @${:.6g} {:s}'.format(amount, self.pair.upper(), price, message))
        res = self.exchange.limitSell(self.pair, amount, price)

        self._cleanupSell(res, message,  timestamp)


    def _cleanupBuy(self, res, message=None, timestamp=None, pair=None):
        if res['status'] == 'error':
            logger.error('Buy failed {} {}'.format(self.pair.upper(), message))
            return

        price = float(res['price'])
        amount = float(res['amount'])

        self.portfolio.deposit(self.pair, amount, price)
        self.portfolio.cash -= amount * price
        self.trades.append([timestamp, price])

        logger.info('Bought {:.7g} {} @${:<.6g} {}'.format(amount, self.pair.upper(), price, message))


    def _cleanupSell(self, res, message, timestamp=None):
        if res['status'] == 'error':
            logger.error('Sell failed {} {}'.format(self.pair.upper(), message))
            return

        price = float(res['price'])
        amount = float(res['amount'])

        self.portfolio.withdraw(self.pair, amount)
        self.portfolio.cash += amount * price
        self.trades[-1] += [timestamp, price]

        logger.info('Sold   {:.7g} {} @${:<.6g} {}'.format(amount, self.pair.upper(), price, message))


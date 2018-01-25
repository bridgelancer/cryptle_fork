from _utility import *
from exchange import *

logger = logging.getLogger(__module__)

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


    def equity(self):
        asset = sum(self.balance_value.values())
        return self.cash + asset



class Strategy:

    # @HARDCODE Remove the exchange default
    # There will be regressions, so fix the, before removing the default
    def __init__(self, pair, portfolio, exchange=None):
        self.init_time = 0
        self.pair = pair
        self.portfolio = portfolio
        self.exchange = exchange or PaperExchange()

        self.trades = []


    def hasBalance(self):
        try:
            return self.portfolio.balance[self.pair] > 0
        except:
            return False


    def hasCash(self):
        return self.portfolio.cash > 0


    def equity(self):
        return self.portfolio.equity()


    def maxBuyAmount(self, price):
        return min(self.equity_at_risk * self.equity() / price, self.portfolio.cash / price)


    def maxSellAmount(self):
        return self.portfolio.balance[self.pair]


    def marketBuy(self, amount, message='', timestamp=None):
        checkType(amount, int, float)
        checkType(message, str)
        assert amount > 0

        logger.debug('Placing market buy for {:.6g} {} {:s}'.format(amount, self.pair.upper(), message))
        res = self.exchange.marketBuy(self.pair, amount)

        self.cleanupBuy(res, message, timestamp)


    def marketSell(self, amount, message='', timestamp=None):
        checkType(amount, int, float)
        checkType(message, str)
        assert amount > 0

        logger.debug('Placing market sell for {:.6g} {} {:s}'.format(amount, self.pair.upper(), message))
        res = self.exchange.marketSell(self.pair, amount)

        self.cleanupSell(res, message, timestamp)


    def limitBuy(self, amount, price, message='', timestamp=None):
        checkType(amount, int, float)
        checkType(price, int, float)
        checkType(message, str)
        assert amount > 0
        assert price > 0

        logger.debug('Placing limit buy for {:.6g} {} @${:.6g} {:s}'.format(amount, self.pair.upper(), price, message))
        res = self.exchange.limitBuy(self.pair, amount, price)

        self.cleanupBuy(res, message, timestamp)


    def limitSell(self, amount, price, message='', timestamp=None):
        checkType(amount, int, float)
        checkType(price, int, float)
        checkType(message, str)
        assert amount > 0
        assert price > 0

        logger.debug('Placing limit sell for {:.6g} {} @${:.6g} {:s}'.format(amount, self.pair.upper(), price, message))
        res = self.exchange.limitSell(self.pair, amount, price)

        self.cleanupSell(res, message,  timestamp)


    def cleanupBuy(self, res, message, timestamp=None):
        if res['status'] == 'error':
            logger.error('Buy failed {} {}'.format(self.pair.upper(), message))
            return

        price = float(res['price'])
        amount = float(res['amount'])

        self.portfolio.deposit(self.pair, amount, price)
        self.portfolio.cash -= amount * price
        self.trades.append([timestamp, price])

        logger.info('Bought {:.7g} {} @${:<.6g} {}'.format(amount, self.pair.upper(), price, message))


    def cleanupSell(self, res, message, timestamp=None):
        if res['status'] == 'error':
            logger.error('Sell failed {} {}'.format(self.pair.upper(), message))
            return

        price = float(res['price'])
        amount = float(res['amount'])

        self.portfolio.withdraw(self.pair, amount)
        self.portfolio.cash += amount * price
        self.trades[-1] += [timestamp, price]

        logger.info('Sold   {:.7g} {} @${:<.6g} {}'.format(amount, self.pair.upper(), price, message))


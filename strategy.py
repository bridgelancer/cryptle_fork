from ta import *
from exchange import *

import inspect
import json
import logging
logger = logging.getLogger('Cryptle')


def checkType(param, *types):
    valid_type = False

    for t in types:
        valid_type |= isinstance(param, t)

    if not valid_type:
        caller = inspect.stack()[1][3]
        passed = type(param).__name__
        expect = types[0].__name__

        fmt = "{} was passed to {} where {} is expected"
        msg = fmt.format(passed, caller, expect)

        raise TypeError(msg)


class Portfolio:

    def __init__(self, cash, balance=None, balance_value=None):
        checkType(cash, int, float)

        self.cash = cash

        if balance is None:
            self.balance = {}
            self.balance_value = {}
        else:
            self.balance = balance
            self.balance_value = balance_value


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
        except ZeroDivisionError:
            pass
        except KeyError:
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
        checkType(pair, str)
        checkType(portfolio, Portfolio)

        self.pair = pair
        self.portfolio = portfolio
        self.is_paper_trade = False

        if exchange == None:
            self.exchange = PaperExchange()
        else:
            self.exchange = exchange

        if isinstance(exchange, PaperExchange):
            self.is_paper_trade = True

        self.prev_crossover_time = None
        self.equity_at_risk = 0.1
        self.timelag_required = 20

        self.prev_sell_time = 0
        self.prev_tick_price = 0


    def hasBalance(self):
        try:
            return self.portfolio.balance[self.pair] > 0
        except:
            return False


    def hasCash(self):
        return self.portfolio.cash > 0


    def equity(self):
        return self.portfolio.equity()


    def marketBuy(self, amount, message=''):
        checkType(amount, int, float)
        checkType(message, str)
        assert amount > 0

        logger.debug('Placing market buy for {:8.5g} {} {:s}'.format(amount, self.pair.upper(), message))
        res = self.exchange.marketBuy(self.pair, amount)

        self.cleanupBuy(res, message)


    def marketSell(self, amount, message=''):
        checkType(amount, int, float)
        checkType(message, str)
        assert amount > 0

        logger.debug('Placing market sell for {:8.5g} {} {:s}'.format(amount, self.pair.upper(), message))
        res = self.exchange.marketSell(self.pair, amount)

        self.cleanupSell(res, message)


    def limitBuy(self, amount, price, message=''):
        checkType(amount, int, float)
        checkType(price, int, float)
        checkType(message, str)
        assert amount > 0
        assert price > 0

        logger.debug('Placing limit buy for {:8.5g} {} @${} {:s}'.format(amount, self.pair.upper(), price, message))
        res = self.exchange.limitBuy(self.pair, amount, price)

        self.cleanupBuy(res, message)


    def limitSell(self, amount, price, message=''):
        checkType(amount, int, float)
        checkType(price, int, float)
        checkType(message, str)
        assert amount > 0
        assert price > 0

        logger.debug('Placing limit sell for {:8.5g} {} @${} {:s}'.format(amount, self.pair.upper(), price, message))
        res = self.exchange.limitSell(self.pair, amount, price)

        self.cleanupSell(res, message)


    def cleanupBuy(self, res, message):
        price = res['price']
        amount = res['amount']

        self.portfolio.deposit(self.pair, amount, price)
        self.portfolio.cash -= amount * price

        logger.info('Bought {:8.5g} {} @${} {}'.format(amount, self.pair.upper(), price, message))


    def cleanupSell(self, res, message):
        price = res['price']
        amount = res['amount']

        self.portfolio.withdraw(self.pair, amount)
        self.portfolio.cash += amount * price

        logger.info('Sold   {:8.5g} {} @${} {}'.format(amount, self.pair.upper(), price, message))


    def unpackTick(self, tick):
        tick = json.loads(tick)
        price = tick['price']
        volume = tick['amount']
        timestamp = float(tick['timestamp'])

        if self.is_paper_trade:
            exchange.price = price
            exchange.timestamp = timestamp

        return price, volume, timestamp


# @DEPRECATED
class OldStrat(Strategy):

    def __init__(self, pair, portfolio):
        super().__init__(pair, portfolio)
        self.five_min = MovingWindow(300)
        self.eight_min = MovingWindow(480)


    def __call__(self, tick):
        price, volume, timestamp = self.unpackTick(tick)

        self.five_min.update(price, volume, timestamp)
        self.eight_min.update(price, volume, timestamp)

        prev_crossover_time = self.prev_crossover_time
        prev_sell_time = self.prev_sell_time

        # @HARDCODE Volume of buy/sell
        if self.hasCash() and not self.hasBalance()  and self.five_min.avg > self.eight_min.avg:
            if prev_crossover_time is None:
                prev_crossover_time = timestamp
            elif timestamp - prev_crossover_time >= self.timelag_required:
                if timestamp - prev_sell_time >= 120:
                    self.marketbuy(1, '[Old strat]')
                    prev_crossover_time = None

        elif self.hasBalance() and self.five_min.avg < self.eight_min.avg:
            if prev_crossover_time is None:
                prev_crossover_time = timestamp
            elif timestamp - prev_crossover_time >= self.timelag_required:
                self.marketSell(1, '[Old strat]', price)
                prev_crossover_time = None
                prev_sell_time = timestamp
        else:
            prev_crossover_time = None

        self.prev_crossover_time = prev_crossover_time
        self.prev_sell_time = prev_sell_time


# @DEPRECATED
class RFStrat(Strategy):

    def __init__(self, pair, portfolio, message='[RF]', period=60, scope1=5, scope2=8):
        super().__init__(pair, portfolio)
        self.five_min = MovingWindow(period * scope1)
        self.eight_min = MovingWindow(period * scope2)
        self.message = message
        self.timelag_required = 30


    def __call__(self, tick):
        price, volume, timestamp = self.unpackTick(tick)

        self.five_min.update(price, volume, timestamp)
        self.eight_min.update(price, volume, timestamp)

        prev_tick_price = self.prev_tick_price
        prev_crossover_time = self.prev_crossover_time
        prev_sell_time = self.prev_sell_time

        if self.hasCash() and not self.hasBalance() and self.five_min.avg > self.eight_min.avg:
            logger.debug('RF identified uptrend')

            if prev_crossover_time is None:
                prev_crossover_time = timestamp
                prev_tick_price = price

            elif timestamp - prev_crossover_time >= self.timelag_required:
                logger.debug('RF identified last crossover was 30 secs ago')

                if timestamp - prev_sell_time >= 120 or price >= 1.0025 * prev_tick_price:

                    amount = self.equity_at_risk * self.equity() / price
                    self.marketBuy(amount, self.message)

                    prev_crossover_time = None
                    prev_tick_price = None

        elif self.hasBalance() and self.five_min.avg < self.eight_min.avg:
            logger.debug('RF identified downtrend')

            if prev_crossover_time is None:
                prev_crossover_time = timestamp

            elif timestamp - prev_crossover_time >= 5:
                self.marketSell(price, self.message)

                prev_crossover_time = None
                prev_sell_time = timestamp

        else:
            prev_crossover_time = None

        self.prev_crossover_time = prev_crossover_time
        self.prev_sell_time = prev_sell_time


# @DEPRECATED
class ATRStrat(Strategy):

    def __init__(self, pair, portfolio, message='[ATR]', period=60, scope1=5, scope2=8):
        super().__init__(pair, portfolio)
        self.five_min = MovingWindow(period * scope1)
        self.eight_min = MovingWindow(period * scope2)
        self.bar = CandleBar(period, scope1)
        self.message = message

        self.upper_atr = 0.5
        self.lower_atr = 0.35


    def __call__(self, tick):
        price, volume, timestamp = self.unpackTick(tick)

        self.five_min.update(price, volume, timestamp)
        self.eight_min.update(price, volume, timestamp)
        self.bar.update(price, timestamp)

        prev_crossover_time = self.prev_crossover_time
        prev_sell_time = self.prev_sell_time

        try:
            atr = self.bar.getAtr()
            belowatr = self.five_min.avg < price - self.lower_atr * atr
            aboveatr = min(self.five_min.avg, self.eight_min.avg) > price + self.upper_atr * atr
        except RuntimeWarning:
            return

        uptrend = self.five_min.avg > self.eight_min.avg
        downtrend = self.five_min.avg < self.eight_min.avg

        # @HARDCODE Buy/Sell message
        if self.hasCash() and not self.hasBalance() and uptrend and belowatr:
            logger.debug('ATR identified uptrend and below ATR band')
            if prev_crossover_time is None:
                prev_crossover_time = timestamp

            elif timestamp - prev_crossover_time >= self.timelag_required:

                amount = self.equity_at_risk * self.equity() / price
                self.marketBuy(amount, self.message)

                prev_crossover_time = None

        elif self.hasBalance() and (downtrend or aboveatr):
            logger.debug('ATR identified downtrend and above ATR band')

            if prev_crossover_time is None:
                prev_crossover_time = timestamp

            elif timestamp - prev_crossover_time >= self.timelag_required:
                self.marketSell(price, self.message)
                prev_crossover_time = None
                prev_sell_time = timestamp

        else:
            prev_crossover_time = None

        self.prev_crossover_time = prev_crossover_time
        self.prev_sell_time = prev_sell_time



class WMAStrat(Strategy):

    def __init__(self, pair, portfolio, message='[WMA]', period=60, scope1=5, scope2=8):
        super().__init__(pair, portfolio)
        self.five_min_bar = CandleBar(period, scope1) # not yet implemented
        self.eight_min_bar = CandleBar(period, scope2) # not yet implemented
        self.message = message

        self.upper_atr = 0.5
        self.lower_atr = 0.35

    def __call__(self, tick):
        price, volume, timestamp = self.unpackTick(tick)

        self.five_min_bar.update(price, timestamp)
        self.eight_min_bar.update(price, timestamp)

        prev_crossover_time = self.prev_crossover_time
        prev_sell_time = self.prev_sell_time

        try:
            atr = self.five_min_bar.getAtr()
            belowatr = self.five_min_bar.WMA < price - self.lower_atr * atr
            aboveatr = min(self.five_min_bar.WMA, self.eight_min_bar.WMA) > price + self.upper_atr * atr
        except RuntimeWarning:
            return

        uptrend = self.five_min_bar.WMA > self.eight_min_bar.WMA
        downtrend = self.five_min_bar.WMA < self.eight_min_bar.WMA

        # @HARDCODE Buy/Sell message
        if self.hasCash() and not self.hasBalance() and uptrend and belowatr:
            logger.debug('WMA identified uptrend and below WMA band')
            if prev_crossover_time is None:
                prev_crossover_time = timestamp

            elif timestamp - prev_crossover_time >= self.timelag_required:

                amount = self.equity_at_risk * self.equity() / price
                self.marketBuy(amount, self.message)

                prev_crossover_time = None

        elif self.hasBalance() and (downtrend or aboveatr):
            logger.debug('WMA identified downtrend and above WMA band')

            if prev_crossover_time is None:
                prev_crossover_time = timestamp

            elif timestamp - prev_crossover_time >= self.timelag_required:
                self.marketSell(price, self.message)
                prev_crossover_time = None
                prev_sell_time = timestamp

        else:
            prev_crossover_time = None

        self.prev_crossover_time = prev_crossover_time
        self.prev_sell_time = prev_sell_time



class VWMAStrat(Strategy):

    def __init__(self, pair, portfolio, message='', period=60, shorttrend=5, longtrend=10):
        super().__init__(pair, portfolio)
        self.message = message

        self.shorttrend = ContinuousVWMA(period * shorttrend)
        self.longtrend = ContinuousVWMA(period * longtrend)
        self.entered = False
        self.prev_trend = True
        self.amount = 0

    def __call__(self, tick):
        price, volume, timestamp = self.unpackTick(tick)

        self.shorttrend.update(price, volume, timestamp)
        self.longtrend.update(price, volume, timestamp)

        if self.prev_crossover_time == None:
            self.prev_crossover_time = timestamp
            return

        trend = self.shorttrend.avg > self.longtrend.avg

        # Checks if there has been a crossing of VWMA
        if self.prev_trend != trend:
            # Set new cross time and latest trend direction (True for up, False for down)
            self.prev_crossover_time = timestamp
            self.prev_trend = trend

            if trend: trend_str = 'upwards'
            else: trend_str = 'downwards'

            logger.debug('VWMA identified crossing ' + trend_str)
            return

        # Filter out temporary breakouts in either direction
        elif timestamp < self.prev_crossover_time + self.timelag_required:
            return

        # Confirm there has been a trend, set more readable variables
        else:
            confirm_up = trend
            confirm_down = not trend

        if not self.entered and self.hasCash() and confirm_up:
            self.amount = self.equity_at_risk * self.equity() / price
            self.marketBuy(self.amount, self.message)
            self.entered = True

        elif self.entered and confirm_down:
            self.marketSell(self.amount, self.message)
            self.entered = False


from ta import *

import json
import logging
logger = logging.getLogger('Cryptle')


class Portfolio:

    def __init__(self, cash, balance=None, balance_value=0):
        self.cash = cash
        self.balance_value = 0

        if balance is None:
            self.balance = {}
        else:
            self.balance = balance
            self.balance_value = balance_value


    def deposit(self, pair, amount):
        try:
            self.balance[pair] += amount
        except KeyError:
            self.balance[pair] = amount


    def withdraw(self, pair, amount):
        try:
            self.balance[pair] -= amount
        except KeyError:
            raise RuntimeWarning('Attempt was made to withdraw from an empty balance')


    def clear(self, pair):
        self.balance[pair] = 0


    def clearAll(self, pair):
        self.balance = {}


    def equity(self):
        return self.cash + self.balance_value



class Strategy:

    def __init__(self, pair, portfolio):
        self.pair = pair
        self.portfolio = portfolio

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


    def buy(self, amount, price, message=''):
        assert isinstance(amount, int) or isinstance(amount, float)
        assert isinstance(message, str)
        assert price > 0

        logger.info('Buy  ' + str(amount) + ' ' + self.pair.upper() + ' @' + str(price) + ' ' + message)
        self.portfolio.deposit(self.pair, amount)
        self.portfolio.cash -= amount * price
        self.portfolio.balance_value += amount * price


    def sell(self, amount, price, message=''):
        assert isinstance(amount, int) or isinstance(amount, float)
        assert isinstance(message, str)
        assert price > 0

        logger.info('Sell '  + str(amount) + ' ' + self.pair.upper() + ' @' + str(price) + ' ' + message)
        self.portfolio.withdraw(self.pair, amount)
        self.portfolio.cash += amount * price
        self.portfolio.balance_value -= amount * price


    def sellAll(self, price, message=''):
        amount = self.portfolio.balance[self.pair]
        self.sell(amount, price, message)


    @staticmethod
    def unpackTick(tick):
        tick = json.loads(tick)
        price = tick['price']
        volume = tick['amount']
        timestamp = float(tick['timestamp'])
        return price, volume, timestamp


# @DEPRECATED
# Hasn't been updated to use the new Strategy/Portfolio API
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

        # @HARDCODE Timelag required
        # @HARDCODE Buy/Sell message
        # @HARDCODE Volume of buy/sell
        if self.hasCash() and not self.hasBalance()  and self.five_min.avg > self.eight_min.avg:
            if prev_crossover_time is None:
                prev_crossover_time = timestamp
            elif timestamp - prev_crossover_time >= self.timelag_required:
                if timestamp - prev_sell_time >= 120:
                    self.buy(1, price, '[Old strat]')
                    prev_crossover_time = None

        elif self.hasBalance() and self.five_min.avg < self.eight_min.avg:
            if prev_crossover_time is None:
                prev_crossover_time = timestamp
            elif timestamp - prev_crossover_time >= self.timelag_required:
                self.sell(1, price, '[Old strat]')
                prev_crossover_time = None
                prev_sell_time = timestamp
        else:
            prev_crossover_time = None

        self.prev_crossover_time = prev_crossover_time
        self.prev_sell_time = prev_sell_time



class RFStrat(Strategy):

    def __init__(self, pair, portfolio, message='[RF]', period=60, scope1=5, scope2=8):
        super().__init__(pair, portfolio)
        self.five_min = MovingWindow(period * scope1)
        self.eight_min = MovingWindow(period * scope2)
        self.message = message


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

            elif timestamp - prev_crossover_time >= 30:
                logger.debug('RF identified last crossover was 30 secs ago')

                if timestamp - prev_sell_time >= 120 or price >= 1.0025 * prev_tick_price:

                    amount = self.equity_at_risk * self.equity() / price
                    self.buy(amount, price, self.message)

                    prev_crossover_time = None
                    prev_tick_price = None

        elif self.hasBalance() and self.five_min.avg < self.eight_min.avg:
            logger.debug('RF identified downtrend')

            if prev_crossover_time is None:
                prev_crossover_time = timestamp

            elif timestamp - prev_crossover_time >= 5:
                self.sellAll(price, self.message)

                prev_crossover_time = None
                prev_sell_time = timestamp

        else:
            prev_crossover_time = None

        self.prev_crossover_time = prev_crossover_time
        self.prev_sell_time = prev_sell_time



class ATRStrat(Strategy):

    def __init__(self, pair, portfolio, message='[ATR]', period=60, scope1=5, scope2=8):
        super().__init__(pair, portfolio)
        self.five_min = MovingWindow(period * scope1)
        self.eight_min = MovingWindow(period * scope2)
        self.bar = CandleBar(period)
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
                self.buy(amount, price, self.message)

                prev_crossover_time = None

        elif self.hasBalance() and (downtrend or aboveatr):
            logger.debug('ATR identified downtrend and above ATR band')

            if prev_crossover_time is None:
                prev_crossover_time = timestamp

            elif timestamp - prev_crossover_time >= self.timelag_required:
                self.sellAll(price, self.message)
                prev_crossover_time = None
                prev_sell_time = timestamp

        else:
            prev_crossover_time = None

        self.prev_crossover_time = prev_crossover_time
        self.prev_sell_time = prev_sell_time

class WMAStrat(Strategy):

    def __init__(self, pair, portfolio, message='[ATR]', period=60, scope1=5, scope2=8):
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
            logger.debug('ATR identified uptrend and below ATR band')
            if prev_crossover_time is None:
                prev_crossover_time = timestamp

            elif timestamp - prev_crossover_time >= self.timelag_required:

                amount = self.equity_at_risk * self.equity() / price
                self.buy(amount, price, self.message)

                prev_crossover_time = None

        elif self.hasBalance() and (downtrend or aboveatr):
            logger.debug('ATR identified downtrend and above ATR band')

            if prev_crossover_time is None:
                prev_crossover_time = timestamp

            elif timestamp - prev_crossover_time >= self.timelag_required:
                self.sellAll(price, self.message)
                prev_crossover_time = None
                prev_sell_time = timestamp

        else:
            prev_crossover_time = None

        self.prev_crossover_time = prev_crossover_time
        self.prev_sell_time = prev_sell_time


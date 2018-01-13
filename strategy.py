from ta import *
from exchange import *
from datetime import datetime

import json
import logging

logger = logging.getLogger('Cryptle')


# @HARDCODE @REGRESSION @TEMPORARY
def appendTimestamp(msg, t):
    return '{} At: {}'.format(msg, datetime.fromtimestamp(t).strftime("%d %H:%M:%S"))


class Portfolio:

    def __init__(self, cash, balance=None, balance_value=None):
        self.cash = cash

        if balance is None:
            self.balance = {}
            self.balance_value = {}
        else:
            self.balance = balance
            self.balance_value = balance_value


    def deposit(self, pair, amount, price=0):

        try:
            self.balance[pair] += amount
            self.balance_value[pair] += amount * price
        except KeyError:
            self.balance[pair] = amount
            self.balance_value[pair] = amount * price


    def withdraw(self, pair, amount):
        try:
            self.balance_value[pair] *= (self.balance[pair] - amount)/ self.balance_value[pair]
            self.balance[pair] -= amount
        except (KeyError, ZeroDivisionError):
            raise RuntimeWarning('Attempt was made to withdraw from an empty balance')


    def clear(self, pair):
        self.balance[pair] = 0


    def clearAll(self, pair):
        self.balance = {}


    def equity(self):
        asset = sum(self.balance_value.values())
        return self.cash + asset



class Strategy:

    # @HARDCODE Remove the exchange default
    # There will be regressions, so fix the, before removing the default
    def __init__(self, pair, portfolio, exchange=None):
        self.pair = pair
        self.portfolio = portfolio

        if (exchange == None):
            self.exchange = PaperExchange()

        self.prev_crossover_time = None
        self.equity_at_risk = 0.1
        self.timelag_required = 30
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


    def buy(self, amount, message='', price=0):
        assert isinstance(amount, int) or isinstance(amount, float)
        assert isinstance(message, str)
        assert price >= 0

        logger.info('Buy  ' + str(amount) + ' ' + self.pair.upper() + ' @' + str(price) + ' ' + message)

        self.portfolio.deposit(self.pair, amount, price)
        self.portfolio.cash -= amount * price

        if price:
            return self.limitBuy(amount, price, message)
        else:
            return self.marketbuy(amount, message)


    def sell(self, amount, message='', price=0):
        assert isinstance(amount, int) or isinstance(amount, float)
        assert isinstance(message, str)
        assert price >= 0

        logger.info('Sell '  + str(amount) + ' ' + self.pair.upper() + ' @' + str(price) + ' ' + message)

        self.portfolio.withdraw(self.pair, amount)
        self.portfolio.cash += amount * price

        if price:
            return self.limitBuy(amount, price, message)
        else:
            return self.marketbuy(amount, message)


    # @Inconsistent interface
    # @Deprecated
    # Fix the interface and it's dependent usage
    def sellAll(self, message='', price=0):
        return self.sell(self.portfolio.balance[self.pair], message, price)


    def marketBuy(self, amount, message=''):
        assert isinstance(amount, int) or isinstance(amount, float)
        assert isinstance(message, str)

        return self.exchange.marketBuy(self.pair, amount)


    def marketSell(self, amount, message=''):
        assert isinstance(amount, int) or isinstance(amount, float)
        assert isinstance(message, str)

        return self.exchange.marketSell(self.pair, amount)


    def limitBuy(self, amount, price, message=''):
        assert isinstance(amount, int) or isinstance(amount, float)
        assert isinstance(message, str)
        assert price > 0

        return self.exchange.limitBuy(self.pair, amount, price)


    def limitBuy(self, amount, price, message=''):
        assert isinstance(amount, int) or isinstance(amount, float)
        assert isinstance(message, str)
        assert price > 0

        return self.exchange.limitSell(self.pair, amount, price)


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
                self.sell(1, '[Old strat]', price)
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
                    self.buy(amount, self.message, price)

                    prev_crossover_time = None
                    prev_tick_price = None

        elif self.hasBalance() and self.five_min.avg < self.eight_min.avg:
            logger.debug('RF identified downtrend')

            if prev_crossover_time is None:
                prev_crossover_time = timestamp

            elif timestamp - prev_crossover_time >= 5:
                self.sellAll(self.message, price)

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
            belowatr = self.bar.WMA < price - self.lower_atr * atr
            aboveatr = min(self.bar.WMA, self.eight_period_bar.WMA) > price + self.upper_atr * atr
            uptrend = self.bar.WMA > self.eight_period_bar.WMA
            downtrend = self.bar.WMA < self.eight_period_bar.WMA
        except RuntimeWarning:
            return

        if self.hasCash() and not self.hasBalance() and uptrend and belowatr:
            logger.debug('ATR identified uptrend and below ATR band')
            if prev_crossover_time is None:
                prev_crossover_time = timestamp

            elif timestamp - prev_crossover_time >= self.timelag_required:

                amount = self.equity_at_risk * self.equity() / price
                self.buy(amount, self.message, price)

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

    def __init__(self, pair, portfolio, message='[WMA]', period=180, scope1=5, scope2=8):
        super().__init__(pair, portfolio)
        self.bar = CandleBar(period)
        self.ATR_5 = ATR(self.bar, scope1)
        self.WMA_5 = WMA(self.bar, scope1)
        self.WMA_8 = WMA(self.bar, scope2)

        self.message = message

        self.upper_atr = 0.5
        self.lower_atr = 0.5

    def __call__(self, tick):
        price, volume, timestamp = self.unpackTick(tick)

        self.bar.update(price, timestamp)

        prev_crossover_time = self.prev_crossover_time
        prev_sell_time = self.prev_sell_time

        try:
            atr = self.ATR_5.atr
            belowatr = max(self.WMA_5.wma, self.WMA_8.wma) < price - self.lower_atr * atr
            aboveatr = min(self.WMA_5.wma, self.WMA_8.wma) > price + self.upper_atr * atr
        except RuntimeWarning:
            return

        uptrend   = self.WMA_5.wma > self.WMA_8.wma
        downtrend = self.WMA_5.wma < self.WMA_8.wma

        # @HARDCODE Buy/Sell message
        if self.hasCash() and not self.hasBalance() and uptrend and belowatr:
            #logger.debug('WMA identified uptrend and below WMA band')
            if prev_crossover_time is None:
                prev_crossover_time = timestamp

            elif timestamp - prev_crossover_time >= self.timelag_required:

                amount = self.equity_at_risk * self.equity() / price
                self.buy(amount, appendTimestamp(self.message, timestamp), price)

                prev_crossover_time = None

        elif self.hasBalance() and (downtrend or aboveatr):
            #logger.debug('WMA identified downtrend and above WMA band')

            if prev_crossover_time is None:
                prev_crossover_time = timestamp

            elif timestamp - prev_crossover_time >= self.timelag_required:
                self.sellAll(appendTimestamp(self.message, timestamp), price)
                prev_crossover_time = None
                prev_sell_time = timestamp

        else:
            prev_crossover_time = None

        self.prev_crossover_time = prev_crossover_time
        self.prev_sell_time = prev_sell_time

class WMAModStrat(Strategy):

    def __init__(self, pair, portfolio, message='[WMA Mod]', period=180, scope1=5, scope2=8):
        super().__init__(pair, portfolio)
        self.bar = CandleBar(period)
        self.ATR_5 = ATR(self.bar, scope1)
        self.WMA_5 = WMA(self.bar, scope1)
        self.WMA_8 = WMA(self.bar, scope2)

        self.message = message

        self.upper_atr = 0.5
        self.lower_atr = 0.5
        self.can_sell = False
        self.entry_time = None


    def __call__(self, tick):
        price, volume, timestamp = self.unpackTick(tick)
        self.bar.update(price, timestamp)
        

        prev_crossover_time = self.prev_crossover_time
        prev_sell_time = self.prev_sell_time
        entry_time = self.entry_time
        can_sell = self.can_sell

        # @ta should not raise RuntimeWarning
        try:
            atr = self.ATR_5.atr

            belowatr = max(self.WMA_5.wma, self.WMA_8.wma) < price - self.lower_atr * atr
            aboveatr = min(self.WMA_5.wma, self.WMA_8.wma) > price + self.upper_atr * atr
        except RuntimeWarning:
            return

        uptrend   = self.WMA_5.wma > self.WMA_8.wma
        downtrend = self.WMA_5.wma < self.WMA_8.wma

        # @HARDCODE Buy/Sell message
        if self.hasCash() and not self.hasBalance() and belowatr:
            #logger.debug('ATR identified uptrend and below ATR band')
            if prev_crossover_time is None:
                prev_crossover_time = timestamp

            elif timestamp - prev_crossover_time >= self.timelag_required:

                amount = self.equity_at_risk * self.equity() / price
                self.buy(amount, appendTimestamp(self.message, timestamp), price)

                prev_crossover_time = None

                if uptrend:
                    can_sell = True
                elif downtrend:
                    can_sell = False
                entry_time = timestamp

        elif self.hasBalance():
            if not can_sell and uptrend:
                can_sell = True
            elif (can_sell and downtrend) or (not can_sell and aboveatr):
                # logger.debug('ATR identified downtrend')
                if prev_crossover_time is None:
                    prev_crossover_time = timestamp

                elif timestamp - prev_crossover_time >= self.timelag_required:
                    self.sellAll(appendTimestamp(self.message, timestamp), price)
                    prev_crossover_time = None
                    prev_sell_time = timestamp
                    entry_time = None

        else:
            prev_crossover_time = None

        self.prev_crossover_time = prev_crossover_time
        self.prev_sell_time = prev_sell_time
        self.entry_time = entry_time
        self.can_sell = can_sell

# To be implemented
class WMADiscreteStrat(Strategy):

    def __init__(self, pair, portfolio, message='[WMA Mod]', period=180, scope1=5, scope2=8):
        super().__init__(pair, portfolio)
        self.bar = CandleBar(period)
        self.ATR_5 = ATR(self.bar, scope1)
        self.WMA_5 = WMA(self.bar, scope1)
        self.WMA_8 = WMA(self.bar, scope2)

        self.message = message

        self.upper_atr = 0.5
        self.lower_atr = 0.5
        self.can_sell = False
        self.entry_time = None


    def __call__(self, tick):
        price, volume, timestamp = self.unpackTick(tick)
        self.bar.update(price, timestamp)
        

        prev_crossover_time = self.prev_crossover_time
        prev_sell_time = self.prev_sell_time
        entry_time = self.entry_time
        can_sell = self.can_sell

        # @ta should not raise RuntimeWarning
        try:
            atr = self.ATR_5.atr

            belowatr = max(self.WMA_5.wma, self.WMA_8.wma) < price - self.lower_atr * atr
            aboveatr = min(self.WMA_5.wma, self.WMA_8.wma) > price + self.upper_atr * atr
        except RuntimeWarning:
            return

        uptrend   = self.WMA_5.wma > self.WMA_8.wma
        downtrend = self.WMA_5.wma < self.WMA_8.wma

        # @HARDCODE Buy/Sell message
        if self.hasCash() and not self.hasBalance() and belowatr:
            #logger.debug('ATR identified uptrend and below ATR band')
            if prev_crossover_time is None:
                prev_crossover_time = timestamp

            elif timestamp - prev_crossover_time >= self.timelag_required:

                amount = self.equity_at_risk * self.equity() / price
                self.buy(amount, appendTimestamp(self.message, timestamp), price)

                prev_crossover_time = None

                if uptrend:
                    can_sell = True
                elif downtrend:
                    can_sell = False
                entry_time = timestamp

        elif self.hasBalance():
            if not can_sell and uptrend:
                can_sell = True
            elif (can_sell and downtrend) or (not can_sell and aboveatr):
                # logger.debug('ATR identified downtrend')
                if prev_crossover_time is None:
                    prev_crossover_time = timestamp

                elif timestamp - prev_crossover_time >= self.timelag_required:
                    self.sellAll(appendTimestamp(self.message, timestamp), price)
                    prev_crossover_time = None
                    prev_sell_time = timestamp
                    entry_time = None

        else:
            prev_crossover_time = None

        self.prev_crossover_time = prev_crossover_time
        self.prev_sell_time = prev_sell_time
        self.entry_time = entry_time
        self.can_sell = can_sell


class VWMAStrat(Strategy):

    def __init__(self, pair, portfolio, message='', period=60, shorttrend=5, longtrend=10):
        super().__init(pair, portfolio)
        self.message = message

        self.shorttrend = MovingWindow(period * ma1)
        self.longtrend = MovingWindow(period * ma2)
        self.entered = False
        self.prev_trend = True

    def __call__(self, tick):
        price, volume, timestamp = self.unpackTick(tick)

        self.shorttrend.update(price, volume, timestamp)
        self.longtrend.update(price, volume, timestamp)

        if self.prev_cross_time == None:
            self.prev_cross_time = timestamp
            return

        trend = self.shorttrend.avg > self.longtrend.avg

        # Checks if there has been a crossing of VWMA
        if self.prev_trend != trend:
            # Set new cross time and latest trend direction (True for up, False for down)
            self.prev_cross_time = timestamp
            self.prev_trend = trend

            if trend: trend_str = 'upwards'
            else: trend_str = 'downwards'

            logger.debug('VWMA identified crossing ' + trend_str)
            return

        # Filter out temporary breakouts in either direction
        elif timestamp < self.prev_cross_time + self.timelag_required:
            return

        # Confirm there has been a trend, set more readable variables
        else:
            confirm_up = trend
            confirm_down = not trend


        if not self.entered and self.hasCash() and confirm_up:
            self.buy(amount, self.message, price)
            self.entered = True

        elif self.entered and confirm_down:
            self.sell(amount, self.message, price)
            self.entered = False

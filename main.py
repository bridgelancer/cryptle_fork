from bitstamp import *
from ta import *

import logging
import time
import sys


logger = logging.getLogger('Cryptle')
logger.setLevel(logging.INFO)

formatter = logging.Formatter('%(name)s: %(asctime)s [%(levelname)s] %(message)s', '%Y-%m-%d %H:%M:%S')

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)

logger.addHandler(ch)


class Portfolio:

    def __init__(self, cash, balance=None):
        self.cash = cash

        if balance is None:
            self.balance = {}
        else:
            self.balance = balance


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



class Strategy:

    # @TODO @CONSIDER Should a portfolio be passed to
    def __init__(self, pair, portfolio):
        self.pair = pair
        self.portfolio = portfolio
        self.equity = 0

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


    # Give message a default value
    def buy(self, amount, price, message=''):
        assert isinstance(amount, int)
        assert isinstance(message, str)
        assert price > 0

        logger.info('Buy  ' + amount + ' ' + self.pair.upper() + ' @' + str(price) + ' ' + message)
        self.portfolio.deposit(self.pair, amount)
        self.portfolio.cash -= amount * price
        self.equity += amount * price


    def sell(self, amount, price, message=''):
        assert isinstance(amount, int)
        assert isinstance(message, str)
        assert price > 0

        logger.info('Sell '  + amount + ' ' + self.pair.upper() + ' @' + str(price) + ' ' + message)
        self.portfolio.withdraw(self.pair, amount)
        self.portfolio.cash += amount * price
        self.equity -= amount * price


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
        self.five_min = MovingWindow(300, pair)
        self.eight_min = MovingWindow(480, pair)


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
                prev_crossover_time = time.time()
            elif time.time() - prev_crossover_time >= self.timelag_required:
                if time.time() - prev_sell_time >= 120:
                    self.buy(1, price, '[Old strat]')
                    prev_crossover_time = None

        elif self.hasBalance() and self.five_min.avg < self.eight_min.avg:
            if prev_crossover_time is None:
                prev_crossover_time = time.time()
            elif time.time() - prev_crossover_time >= self.timelag_required:
                self.sell(1, price, '[Old strat]')
                prev_crossover_time = None
                prev_sell_time = time.time()
        else:
            prev_crossover_time = None

        self.prev_crossover_time = prev_crossover_time
        self.prev_sell_time = prev_sell_time



class RFStrat(Strategy):

    def __init__(self, pair, portfolio):
        super().__init__(pair, portfolio)
        self.five_min = MovingWindow(300)
        self.eight_min = MovingWindow(480)


    def __call__(self, tick):
        price, volume, timestamp = self.unpackTick(tick)

        self.five_min.update(price, volume, timestamp)
        self.eight_min.update(price, volume, timestamp)

        prev_tick_price = self.prev_tick_price
        prev_crossover_time = self.prev_crossover_time
        prev_sell_time = self.prev_sell_time

        # @HARDCODE Buy/Sell message
        if self.hasCash() and not self.hasBalance() and self.five_min.avg > self.eight_min.avg:
            if prev_crossover_time is None:
                prev_crossover_time = time.time()
                prev_tick_price = price

            elif time.time() - prev_crossover_time >= 30:
                if time.time() - prev_sell_time >= 120 or price >= 1.0025 * prev_tick_price:

                    amount = self.equity_at_risk * self.equity
                    self.buy(amount, price, '[RF strat]')

                    prev_crossover_time = None
                    prev_tick_price = None

        elif self.hasBalance() and self.five_min.avg < self.eight_min.avg:

            if prev_crossover_time is None:
                prev_crossover_time = time.time()

            elif time.time() - prev_crossover_time >= 5:
                self.sellAll(price, '[RF strat]')
                prev_crossover_time = None
                prev_sell_time = time.time()

        else:
            prev_crossover_time = None

        self.prev_crossover_time = prev_crossover_time
        self.prev_sell_time = prev_sell_time



class ATRStrat(Strategy):

    def __init__(self, pair, portfolio):
        super().__init__(pair, portfolio)
        self.five_min = MovingWindow(300)
        self.eight_min = MovingWindow(480)
        self.bar = CandleBar(60)

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
            atr = self.bar.get_atr()
            belowatr = self.five_min.avg < price - self.lower_atr * atr
            aboveatr = min(self.five_min.avg, self.eight_min.avg) > price + self.upper_atr * atr
        except RuntimeWarning:
            return

        uptrend = self.five_min.avg > self.eight_min.avg
        downtrend = self.five_min.avg < self.eight_min.avg

        # @HARDCODE Buy/Sell message
        # @HARDCODE Volume of buy/sell
        if self.hasCash() and not self.hasBalance() and uptrend and belowatr:
            if prev_crossover_time is None:
                prev_crossover_time = time.time()

            elif time.time() - prev_crossover_time >= self.timelag_required:

                amount = self.equity_at_risk * self.equity
                self.buy(amount, price, '[ATR strat]')

                prev_crossover_time = None

        elif self.hasBalance() and (downtrend or aboveatr):

            if prev_crossover_time is None:
                prev_crossover_time = time.time()

            elif time.time() - prev_crossover_time >= self.timelag_required:
                self.sellAll(price, '[ATR strat]')
                prev_crossover_time = None
                prev_sell_time = time.time()

        else:
            prev_crossover_time = None

        self.prev_crossover_time = prev_crossover_time
        self.prev_sell_time = prev_sell_time



class TestStrat(Strategy):

    def __call__(self, tick):
        price, volume, timestamp = self.unpackTick(tick)
        self.buy(1, 'Testing Buy', price)
        self.sell(1, 'Testing Sell', price)



def update_candle(bar, tick):
    tick = json.loads(tick)
    price = tick['price']
    timestamp = float(tick['timestamp'])

    bar.update(price, timestamp)


def main(pair='ethusd'):
    bs = BitstampFeed()

    port1 = Portfolio(10000)
    port2 = Portfolio(10000)
    port3 = Portfolio(10000)

    # Add a few more strat instances and tweak their parameters to test run
    rf   = RFStrat(pair, port2)
    atr  = ATRStrat(pair, port3)

    bs.onTrade(pair, lambda x: logger.debug('Recieved new tick'))
    bs.onTrade(pair, rf)
    bs.onTrade(pair, atr)

    while True:
        logger.info('RF Cash: ' + str(port2.cash))
        logger.info('RF Balance: ' + str(port2.balance))
        logger.info('ATR Cash: ' + str(port3.cash))
        logger.info('ATR Balance: ' + str(port3.balance))
        time.sleep(30)


if __name__ == '__main__':
    print('Hello crypto!')
    try:
        pair = sys.argv[1]

        fh = logging.FileHandler(pair + '.log')
        fh.setFormatter(formatter)
        logger.addHandler(fh)

        main(pair)
    except:
        main()


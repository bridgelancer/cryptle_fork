import sys
import logging
import time
import json
import hmac
import hashlib
import logging

import pysher
import requests as req


logger = logging.getLogger('Cryptle')
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(name)s: %(asctime)s [%(levelname)s] %(message)s', '%Y-%m-%d %H:%M:%S')
ch.setFormatter(formatter)

logger.addHandler(ch)


class BitstampREST:

    def __init__(self, key=None, secret=None, customer_id=None):
        self.key = key
        self.secret = secret
        self.id = customer_id
        self.url = 'https://www.bitstamp.net/api/v2'


    def getTicker(self, pair):
        assert isinstance(pair, str)
        return self._get('/ticker/' + pair)


    def getOrderbook(self, pair):
        assert isinstance(pair, str)
        return self._get('/order_book/' + pair)


    def getBalance(self):
        assert self.secret is not None
        params = self._authParams()
        return self._post('/balance/', params=params)


    def getOrderStatus(self, order_id):
        assert isinstance(order_id, int)
        params = self._authParams()
        params['id'] = order_id
        return self._post('/order_status', params=params)


    def limitBuy(self, pair, amount, price):
        assert isinstance(pair, str)
        assert amount > 0
        assert price > 0

        params = self._authParams()
        params['amount'] = amount
        params['price'] = price
        return self._post('/buy/' + pair, params=params)


    def limitSell(self, pair, amount, price):
        assert isinstance(pair, str)
        assert amount > 0
        assert price > 0

        params = self._authParams()
        params['amount'] = amount
        params['price'] = price
        return self._post('/sell/' + pair, params=params)


    def marketBuy(self, pair, amount):
        assert isinstance(pair, str)
        assert amount > 0

        params = self._authParams()
        params['amount'] = amount
        return self._post('/buy/market/' + pair, params=params)


    def marketSell(self, pair, amount):
        assert isinstance(pair, str)
        assert amount > 0

        params = self._authParams()
        params['amount'] = amount
        return self._post('/sell/market/' + pair, params=params)


    def cancnelOrder(self, order_id):
        assert isinstance(order_id, int)
        params = self._authParams()
        params['id'] = price
        return self._post('/order_status', params=params)


    def _get(self, endpoint, params=None):
        assert isinstance(endpoint, str)
        assert params is None or isinstance(params, dict)

        res = req.get(self.url + endpoint, params)
        c = res.status_code

        if c == 400:
            logger.error('400 Bad Request Error')
            raise ConnectionError('Server 400 Bad Request Error')
        elif c == 404:
            logger.error('404 Page Not Found')
            raise ConnectionError('Server 404 Page Not Found')
        elif c != 200:
            raise ConnectionError('Server returned error ' + str(c))

        parsed_res = json.loads(res.text)
        return parsed_res


    def _post(self, endpoint, params):
        assert isinstance(endpoint, str)
        assert isinstance(params, dict)

        res = req.post(self.url + endpoint, params)
        c = res.status_code

        if c == 400:
            logger.error('400 Bad Request Error')
            raise ConnectionError('Server 400 Bad Request Error')
        elif c == 401:
            logger.error('401 Unauthorized Error')
            raise ConnectionError('Server 401 Unauthorized Error')
        elif c == 403:
            logger.error('403 Bad Request Error')
            raise ConnectionError('Server 403 Forbidden')
        elif c == 404:
            logger.error('404 Page Not Found')
        elif c != 200:
            raise ConnectionError('Server returned error ' + str(c))

        parsed_res = json.loads(res.text)
        return parsed_res


    def _authParams(self):
        assert self.secret is not None

        nonce = int(time.time())
        params = {}
        params['key'] = self.key
        params['signature'] = self._sign(str(nonce))
        params['nonce'] = nonce
        return params


    def _sign(self, nonce):
        message = nonce + self.id + self.key
        signature = hmac.new(
                self.secret.encode('utf-8'),
                msg=message.encode('utf-8'),
                digestmod=hashlib.sha256
        ).hexdigest().upper()
        return signature



class BitstampFeed:

    def __init__(self):
        api_key = 'de504dc5763aeef9ff52'

        self.pusher = pysher.Pusher(api_key)
        self.pusher.connect()
        time.sleep(2)


    def onTrade(self, pair, callback):
        assert callable(callback)
        self._bindSocket('live_trades_' + pair, 'trade', callback)


    def onOrderCreate(self, pair, callback):
        assert callable(callback)
        self._bindSocket('live_orders_' + pair, 'order_created', callback)


    def _bindSocket(self, channel_name, event, callback):

        if channel_name not in self.pusher.channels:
            self.pusher.subscribe(channel_name)

        channel = self.pusher.channels[channel_name]
        channel.bind(event, callback)



class MovingWindow:

    # window is the number of seconds in the lookback window
    # Ticker (optional) is meta-info about what series is being tracked
    def __init__(self, window, ticker=None):
        self._ticks = [] # @OPTIMIZE use NumPy arrays

        self.avg = 0
        self.volume = 0
        self.dollar_volume = 0

        self.window = window
        self.ticker = ticker


    def __str__(self):
        return self.ticker


    def update(self, price, volume, timestamp=None):

        if timestamp == None:
            timestamp = time.time()

        self.last = price
        self.volume = self.volume + volume
        self.dollar_volume = self.dollar_volume + price * volume
        self.avg = self.dollar_volume / self.volume

        self._ticks.append((price, volume, timestamp))
        self.clear()

    def clear(self):
        now = time.time()
        lookback = now - self.window

        while True:
            if self._ticks[0][2] < lookback:
                tick = self._ticks.pop(0)
                self.volume = self.volume - tick[1]
                self.dollar_volume = self.dollar_volume - tick[0] * tick[1]
                self.avg = self.dollar_volume / self.volume
            else:
                break


    def high(self):
        return max(self._ticks)


    def low(self):
        return min(self._ticks)



class CandleBar:
    # _bars: List of (open, close, high, low, nth minute bar)
    # This class is for storing the min-by-min bars the minute before the current tick
    # default bar size is 1 minute
    def __init__(self, period=60):
        self._bars = []

        self.period = period
        self.lookback = 100
        self.last = 0

        self.ls = []
        self.atr_val = 0
        
        self.barmin = None
        self.barmax = None
        self.baropen = None
        self.barclose = None
        self.timestamp_last = None

    def update(self, price, timestamp=None):
        
        if timestamp == None:
            timestamp = time.time()
        # execute the following block if
        # - the current trade happens 60s after the last trade OR
        # - the current trade falls in the following 60s window
        if self.timestamp_last == None:
            self.barmin = self.barmax = self.baropen = self.barclose = price
            self.timestamp_last = timestamp
        elif int(timestamp / self.period) != int(self.timestamp_last / self.period):
            self._bars.append([self.baropen, self.barclose, self.barmax, self.barmin, int(timestamp/self.period) + 1])
            logger.debug(self._bars[-1])
            self.timestamp_last = timestamp

            self.barmin = self.barmax = self.baropen = self.barclose = price
        elif int(timestamp / self.period) == int(self.timestamp_last / self.period):
            self.barmin = min(self.barmin, price)
            self.barmax = max(self.barmax, price)
            self.barclose = price

        self.last = price  # update the current tick prcie

        # @HARDCODE
        self.compute_atr(5)
        self.prune(self.lookback)


    def compute_atr(self, mins):
        if (len(self._bars) <= mins and len(self._bars) > 0):
            self.ls.append(self._bars[-1][2] - self._bars[-1][3])
            self.atr_var = sum(self.ls) / len(self.ls)
        elif(len(self._bars) > mins):
            self.ls.clear()
            TR = self._bars[-1][2] - self._bars[-1][3]
            self.atr_val = (self.atr_val * (mins - 1) + TR) / mins

    def get_atr(self):

        #@HARDCODE
        if (len(self._bars) >= 5):
            return self.atr_val
        else:
            raise RuntimeWarning("ATR not yet available")

    def prune(self, lookback): #discard the inital bars after 100 periods of bar data
        if len(self._bars) != 0:
            self._bars = self._bars[-min(len(self._bars), lookback):]



class Portfolio:

    def __init__(self, starting_cash, starting_balance=None):
        self.cash = starting_cash
        if starting_balance is None:
            self.balance = {}
        else:
            self.balance = starting_balance


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
    def buy(self, amount, message, price):
        assert isinstance(amount, int)
        assert isinstance(message, str)
        assert price > 0

        logger.info('Buy  ' + self.pair.upper() + ' @' + str(price) + ' ' + message)
        self.portfolio.deposit(self.pair, amount)
        self.portfolio.cash -= price


    def sell(self, amount, message, price):
        assert isinstance(amount, int)
        assert isinstance(message, str)
        assert price > 0

        logger.info('Sell ' + self.pair.upper() + ' @' + str(price) + ' ' + message)
        self.portfolio.withdraw(self.pair, amount)
        self.portfolio.cash += price


    @staticmethod
    def unpackTick(tick):
        tick = json.loads(tick)
        price = tick['price']
        volume = tick['amount']
        timestamp = float(tick['timestamp'])
        return price, volume, timestamp



class Strat(Strategy):

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

        if self.hasCash() and not self.hasBalance()  and self.five_min.avg > self.eight_min.avg:
            if prev_crossover_time is None:
                prev_crossover_time = time.time()
            elif time.time() - prev_crossover_time >= self.timelag_required:
                if time.time() - prev_sell_time >= 120:
                    self.buy(1, '[Old strat]', price)
                    prev_crossover_time = None

        elif self.hasBalance() and self.five_min.avg < self.eight_min.avg:
            if prev_crossover_time is None:
                prev_crossover_time = time.time()
            elif time.time() - prev_crossover_time >= self.timelag_required:
                self.sell(1, '[Old strat]', price)
                prev_crossover_time = None
                prev_sell_time = time.time()
        else:
            prev_crossover_time = None

        self.prev_crossover_time = prev_crossover_time
        self.prev_sell_time = prev_sell_time



class ATRStrat(Strategy):

    def __init__(self, pair, portfolio):
        super().__init__(pair, portfolio)
        self.five_min = MovingWindow(300, pair)
        self.eight_min = MovingWindow(480, pair)
        self.bar = CandleBar(60)
        self.atr_shift = 0.5


    def __call__(self, tick):
        price, volume, timestamp = self.unpackTick(tick)

        self.five_min.update(price, volume, timestamp)
        self.eight_min.update(price, volume, timestamp)
        self.bar.update(price, timestamp)

        prev_crossover_time = self.prev_crossover_time
        prev_sell_time = self.prev_sell_time

        try:
            bound = self.atr_shift * self.bar.get_atr()
        except RuntimeWarning:
            return

        uptrend = self.five_min.avg > self.eight_min.avg
        downtrend = self.five_min.avg < self.eight_min.avg

        if self.hasCash() and not self.hasBalance() and uptrend and self.five_min.avg < price - bound:
            if prev_crossover_time is None:
                prev_crossover_time = time.time()
            elif time.time() - prev_crossover_time >= self.timelag_required:
                    self.buy(1, '[ATR strat]', price)
                    prev_crossover_time = None

        elif self.hasBalance() and (downtrend or min(self.five_min.avg, self.eight_min.avg) > price+ bound):
            if prev_crossover_time is None:
                prev_crossover_time = time.time()
            elif time.time() - prev_crossover_time >= self.timelag_required:
                self.sell(1, '[ATR strat]', price)
                prev_crossover_time = None
                prev_sell_time = time.time()
        else:
            prev_crossover_time = None

        self.prev_crossover_time = prev_crossover_time
        self.prev_sell_time = prev_sell_time



class RFStrat(Strategy):

    def __init__(self, pair, portfolio):
        super().__init__(pair, portfolio)
        self.five_min = MovingWindow(300, pair)
        self.eight_min = MovingWindow(480, pair)


    def __call__(self, tick):
        price, volume, timestamp = self.unpackTick(tick)

        self.five_min.update(price, volume, timestamp)
        self.eight_min.update(price, volume, timestamp)

        prev_tick_price = self.prev_tick_price
        prev_crossover_time = self.prev_crossover_time
        prev_sell_time = self.prev_sell_time

        if self.hasCash() and not self.hasBalance() and self.five_min.avg > self.eight_min.avg:
            if prev_crossover_time is None:
                prev_crossover_time = time.time()
                prev_tick_price = price

            elif time.time() - prev_crossover_time >= 30:
                if time.time() - prev_sell_time >= 120 or price >= 1.0025 * prev_tick_price:
                    self.buy(1, '[RF strat]', price)
                    prev_crossover_time = None
                    prev_tick_price = None

        elif self.hasBalance() and self.five_min.avg < self.eight_min.avg:
            if prev_crossover_time is None:
                prev_crossover_time = time.time()
            elif time.time() - prev_crossover_time >= 5:
                self.sell(1, '[RF strat]', price)
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

    port1 = Portfolio(100)
    port2 = Portfolio(100)
    port3 = Portfolio(100)

    old  = Strat(pair, port1)
    rf   = RFStrat(pair, port2)
    atr  = ATRStrat(pair, port3)

    bs.onTrade(pair, lambda x: logger.debug('Recieved new tick'))
    bs.onTrade(pair, old)
    bs.onTrade(pair, rf)
    bs.onTrade(pair, atr)

    while True:
        logger.debug('Old Cash: ' + str(port1.cash))
        logger.debug('Old Balance: ' + str(port1.balance))
        logger.debug('RF Cash: ' + str(port2.cash))
        logger.debug('RF Balance: ' + str(port2.balance))
        logger.debug('ATR Cash: ' + str(port3.cash))
        logger.debug('ATR Balance: ' + str(port3.balance))
        time.sleep(30)


if __name__ == '__main__':
    print('Hello crypto!')
    try:
        pair = sys.argv[1]
        fh = logging.FileHandler(pair + '.csv')
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        main(pair)
    except:
        main()


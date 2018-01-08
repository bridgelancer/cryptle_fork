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

fh = logging.FileHandler('cryptle.log', mode='w')
fh.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(name)s: %(asctime)s [%(levelname)s] %(message)s', '%Y-%m-%d %H:%M:%S')
fh.setFormatter(formatter)
ch.setFormatter(formatter)

logger.addHandler(fh)
logger.addHandler(ch)


class BitstampREST:

    def __init__(self, key=None, secret=None, customer_id=None):
        self.key = key
        self.secret = secret
        self.id = customer_id
        self.url = 'https://www.bitstamp.net/api/v2'


    def getTicker(self, pair):
        return self._get('/ticker/' + pair)


    def getOrderbook(self, pair):
        return self._get('/order_book/' + pair)


    def getBalance(self):
        params = self._authParams()
        return self._post('/balance/', params=params)


    def getOrderStatus(self, order_id):
        params = self._authParams()
        params['id'] = order_id
        return self._post('/order_status', params=params)


    def limitBuy(self, pair, amount, price):
        params = self._authParams()
        params['amount'] = amount
        params['price'] = price
        return self._post('/buy/' + pair, params=params)


    def limitSell(self, pair, amount, price):
        params = self._authParams()
        params['amount'] = amount
        params['price'] = price
        return self._post('/sell/' + pair, params=params)


    def marketBuy(self, pair, amount):
        params = self._authParams()
        params['amount'] = amount
        return self._post('/buy/market/' + pair, params=params)


    def marketSell(self, pair, amount):
        params = self._authParams()
        params['amount'] = amount
        return self._post('/sell/market/' + pair, params=params)


    def cancnelOrder(self, order_id):
        params = self._authParams()
        params['id'] = price
        return self._post('/order_status', params=params)


    def _get(self, endpoint, params=None):
        assert params is None or isinstance(params, dict)

        res = req.get(self.url + endpoint, params)
        c = res.status_code

        if c != 200:
            raise ConnectionError('Server returned error ' + str(c))

        parsed_res = json.loads(res.text)
        return parsed_res


    def _post(self, endpoint, params):
        assert isinstance(params, dict)

        res = req.post(self.url + endpoint, params)
        c = res.status_code

        if c != 200:
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
        self._bindSocket('live_orders' + pair, 'order_created', callback)


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
        self.last = 0
        self.timestamp_last = time.time()
        self.ticks = []

        self.ls = []

    def update(self, price, timestamp=None):

        if timestamp == None:
            timestamp = time.time()

        # execute the following block if
        # - the current trade happens 60s after the last trade OR
        # - the current trade falls in the following 60s window
        if int(timestamp / 60) < int(self.timestamp_last / 60):

            self._min = min(item[0] for item in self.ticks)
            self._max = max(item[0] for item in self.ticks)
            self._open = self.ticks[0][0]
            self._close = self.ticks[-1][0]
            self.last = price  # update the current tick prcie

            self._bars.append([self._open, self._close, self._max, self._min, int(self.timestamp_last/self.period) + 1])

            self.ticks.clear()
            self.timestamp_last = timestamp

            if not len(self._bars) == 0:
                logger.debug(self._bars[-1])
            
            self.compute_atr(5)

        self.ticks.append([price, timestamp])

    def compute_atr(self, period):

        if (len(self._bars) <= period):
            self.ls.append(self._bars[-1][2] - self._bars[-1][3])
            self.atr_var = sum(ls) / len(ls)
        elif(len(self._bars) > period):
            self.ls.clear()
            TR = self._bars[-1][2] - self._bars[-1][3]
            self.atr_val = (self.atr_var * (period - 1) + TR) / period
    
    def get_atr(self):
    
    if (self._bars > period):
        return self.atr_val
    else
        raise RuntimeWarning("ATR not yet available")

    def prune(self, lookback): #discard the inital entries after 100 periods
        self._bars = self._bars[-lookback:]



class Portfolio:

    def __init__(self, starting_cash, starting_balance={}):
        self.cash = starting_cash
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
        self.five_min = MovingWindow(300, pair)
        self.eight_min = MovingWindow(480, pair)
        self.bar = CandleBar()

        self.portfolio = portfolio

        self.prev_crossover_time = None
        self.equity_at_risk = 0.1
        self.timelag_required = 20

        self.prev_sell_time = None
        self.prev_tick_price = None

        self.atr_shift = 0.5


    # @TODO @REFACTOR @HARDCODE
    # One instance of Strategy can only ever use strat_a or strat_b in callbacks
    # Use proper portfolio management to determine amount to buy/sell
    def trade_strategy_rf(self, tick):
        tick = json.loads(tick)
        price = tick['price']
        volume = tick['amount']
        timestamp = float(tick['timestamp'])

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
                    self.buy(1, '[New strat]', price)
                    prev_crossover_time = None
                    prev_tick_price = None

        elif self.hasBalance() and self.five_min.avg < self.eight_min.avg:
            if prev_crossover_time is None:
                prev_crossover_time = time.time()
            elif time.time() - prev_crossover_time >= 5:
                self.sell(1, '[New strat]', price)
                prev_crossover_time = None
                prev_sell_time = time.time()
        else:
            prev_crossover_time = None

        self.prev_crossover_time = prev_crossover_time
        self.prev_sell_time = prev_sell_time


    def trade_strategy_original(self, tick):
        tick = json.loads(tick)
        price = tick['price']
        volume = tick['amount']
        timestamp = float(tick['timestamp'])

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

    def trade_strategy_atr(self, tick):
        tick = json.loads(tick)
        price = tick['price']
        volume = tick['amount']
        timestamp = float(tick['timestamp'])

        self.five_min.update(price, volume, timestamp)
        self.eight_min.update(price, volume, timestamp)

        prev_crossover_time = self.prev_crossover_time
        prev_sell_time = self.prev_sell_time

        if self.hasCash() and not self.hasBalance() and self.five_min.avg > self.eight_min.avg and self.five_min.avg < price - self.atr_shift * self.five_min.atr(60):
            if prev_crossover_time is None:
                prev_crossover_time = time.time()
            elif time.time() - prev_crossover_time >= self.timelag_required:
                    self.buy(1, '[ATR strat]', price)
                    prev_crossover_time = None

        elif self.hasBalance() and self.five_min.avg < self.eight_min.avg or min(self.five_min.avg, self.eight_min.avg) > price + self.atr_shift * self.five_min.atr(60):
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

    def hasBalance(self):
        try:
            return self.portfolio.balance[self.pair] > 0
        except:
            return False


    def hasCash(self):
        return self.portfolio.cash > 0

    # @HARDCODE @REMOVE
    # Portfolio needs to be updated properly
    # Price should be acquired from the exchange
    # Give message a default value
    def buy(self, amount, message, price):
        assert isinstance(amount, int)
        assert isinstance(message, str)
        logger.info('Buy  ' + self.pair.upper() + '@' + str(price) + ' ' + message)
        self.portfolio.deposit(self.pair, amount)
        self.portfolio.cash -= price


    def sell(self, amount, message, price):
        assert isinstance(amount, int)
        assert isinstance(message, str)
        logger.info('Sell ' + self.pair.upper() + '@' + str(price) + ' ' + message)
        self.portfolio.withdraw(self.pair, amount)
        self.portfolio.cash += price


    def test(self, tick):
        tick = json.loads(tick)
        price = tick['price']
        volume = tick['amount']
        timestamp = float(tick['timestamp'])

        self.buy(1, 'Testing Buy', price)
        self.sell(1, 'Testing Sell', price)


def update_candle(bar, tick):
    tick = json.loads(tick)
    price = tick['price']
    timestamp = float(tick['timestamp'])

    bar.update(price, timestamp)


def main():
    bs = BitstampFeed()

    port1 = Portfolio(100)
    port2 = Portfolio(100)
    port3 = Portfolio(100)
    port4 = Portfolio(100)

    eth_strat_new = Strategy('ethusd', port1)
    eth_strat_old = Strategy('ethusd', port2)
    eth_strat_rf  = Strategy('ethusd', port3)
    eth_strat_test  = Strategy('ethusd', port3)

    bs.onTrade('ethusd', lambda x: logger.debug('Recieved new tick'))
    bs.onTrade('ethusd', eth_strat_test.test)
    bs.onTrade('ethusd', eth_strat_new.trade_strategy_atr)
    bs.onTrade('ethusd', eth_strat_old.trade_strategy_original)
    bs.onTrade('ethusd', eth_strat_rf.trade_strategy_rf)


    while True:
        time.sleep(1)


if __name__ == '__main__':
    print('Hello crypto!')
    main()


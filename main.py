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
ch.setLevel(logging.INFO)

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


    def atr(self, period):
        now = time.time()

        lookback_1 = now - period
        lookback_2 = now - 2 * period

        this_minute = [x[0] for x in self._ticks if x[2] > lookback_1]
        prev_minute = [x[0] for x in self._ticks if x[2] < lookback_1 and x[2] > lookback_2]

        bound_high = max(this_minute[0], this_minute[-1])
        bound_low  = max(this_minute[0], this_minute[-1])

        true_range_this = max(max(this_minute) - bound_low, bound_high - min(this_minute))
        true_range_prev = max(prev_minute) - min(prev_minute)

        return (true_range_prev * (self.window/period- 1) + true_range_this) / (self.window/period)


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
    # max_lookback is number of bars to store
    def __init__(self, period=60, max_lookback=100):
        self._bars = []
        self._max_lookback = max_lookback

        self.period = period
        self.last = 0
        self.timestamp_last = time.time()
        self.ticks = []

    def update(self, price, timestamp=None):

        if timestamp == None:
            timestamp = time.time()

        # execute the following block if the current trade happens 60s after the last trade OR
        #                             if the current trade falls in the following 60s window
        #                                 with the window defined to start at initialization
        if (timestamp - self.timestamp_last) >= self.period or (timestamp % self.period)  < (self.timestamp_last % self.period):

            logger.debug("Updating candle bar...")

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

        self.ticks.append([price, timestamp])

    def prune(self): #discard the inital entries after 100 periods
        self._bars = self._bars[-self._max_lookback:]



class Portfolio:

    def __init__(self, starting_cash, starting_balance={}):
        self.cash = starting_cash
        self.balance = starting_balance


class Strategy:
    def __init__(self, pair):
        self.pair = pair
        self.five_min = MovingWindow(300, pair)
        self.eight_min = MovingWindow(480, pair)
        self.bar = CandleBar()

        self.portfolio = Portfolio() ## @TODO whether to keep individual coin portfolio

        self.prev_crossover_time = None
        self.equity_at_risk = 0.1
        self.timelag_required = 10

    def trade_strategy(self, tick):
        tick = json.loads(tick)
        price = tick['price']
        volume = tick['amount']
        timestamp = float(tick['timestamp'])

        self.five_min.update(price, volume, timestamp)
        self.eight_min.update(price, volume, timestamp)

        prev_crossover_time = self.prev_crossover_time

        if self.portfolio.balance[self.pair] == 0 and self.five_min.avg > self.eight_min.avg:
            if prev_crossover_time is None:
                prev_crossover_time = time.time()
            elif time.time() - prev_crossover_time >= 10:
                logger.info('Bought XRP @' + str(price))
                self.portfolio.amount = 00
                prev_crossover_time = None

        elif self.portfolio.balance[self.pair] > 0 and self.five_min.avg < self.eight_min.avg:
            if prev_crossover_time is None:
                prev_crossover_time = time.time()
            elif time.time() - prev_crossover_time >= 10:
                logger.info('Sold XRP @' + str(price))
                self.portfolio.amount = 0
                prev_crossover_time = None

        else:
            prev_crossover_time = None

        self.prev_crossover_time = prev_crossover_time


def update_candle(bar, tick):
    tick = json.loads(tick)
    price = tick['price']
    timestamp = float(tick['timestamp'])

    bar.update(price, timestamp)


def main():
    bs = BitstampFeed()
    bar = CandleBar()
    eth_strat = Strategy('ethusd')

    bs.onTrade('ethusd', lambda x: logger.debug('Recieved new tick'))
    bs.onTrade('ethusd', lambda x: update_candle(bar, x))
    bs.onTrade('ethusd', eth_strat.trade_strategy)

    while True:
        time.sleep(1)


if __name__ == '__main__':
    print('Hello crypto!')
    main()


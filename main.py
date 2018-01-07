import numpy as np
import pandas as pd
import requests as req
import json
import time

import pysher
import hmac
import hashlib


class BitstampREST:

    def __init__(self, key=None, secret=None, customer_id=None):
        self.key = key
        self.secret = secret
        self.id = customer_id
        self.url = 'https://www.bitstamp.net/api/v2'


    def getTicker(self, pair):
        return _get('/ticker/' + pair)


    def getOrderbook(self, pair):
        return _get('/order_book/' + pair)


    def getBalance(self):
        params = self._authParams()
        return _post('/balance/', params=params)


    def getOrderStatus(self, order_id):
        params = self._authParams()
        params['id'] = order_id
        return _post('/order_status', params=params)


    def limitBuy(self, pair, amount, price):
        params = self._authParams()
        params['amount'] = amount
        params['price'] = price
        return _post('/buy/' + pair, params=params)


    def limitSell(self, pair, amount, price):
        params = self._authParams()
        params['amount'] = amount
        params['price'] = price
        return _post('/sell/' + pair, params=params)


    def marketBuy(self, pair, amount):
        params = self._authParams()
        params['amount'] = amount
        return _post('/buy/market/' + pair, params=params)


    def marketSell(self, pair, amount):
        params = self._authParams()
        params['amount'] = amount
        return _post('/sell/market/' + pair, params=params)


    def cancnelOrder(self, order_id):
        params = self._authParams()
        params['id'] = price
        return _post('/order_status', params=params)


    def _get(endpoint, params=None):
        assert params is None or isinstance(params, dict)

        res = req.get(self.url + endpoint, pararms)
        c = res.status_code

        if c != 200:
            raise ConnectionError('Server returned error ' + str(c))

        parsed_res = json.loads(res.text)
        return parsed_res


    def _post(endpoint, params):
        assert isinstance(params, dict)

        res = req.post(self.url + endpoint, pararms)
        c = res.status_code

        if c != 200:
            raise ConnectionError('Server returned error ' + str(c))

        parsed_res = json.loads(res.text)
        return parsed_res


    def _authParams(self):
        assert self.secret is not None

        nonce = time.time()
        params = {}
        params['key'] = self.key
        params['signature'] = self._sign(nonce)
        params['nonce'] = nonce
        return params


    def _sign(self, nonce):
        message = nonce + self.id + self.key
        signature = hmac.new(
                self.secret,
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


    # Consider initializing url for HTTPS API functions
    self.url = 'https://www.bitstamp.net/api/v2/'

    def postMarketOrder(self, nonce, amount, pair):
        action = 'buy/market'

        http = self.url + action + pair #where pair should be a string of currency pair (in format of '/btcusd/')

        res = request.post(http, param = {'key': self.key, 'signature': _sign(self, nonce), 'nonce': nonce, 'amount': amount})

    def postLimitOrder(self, nonce, price, amount, limit_price, pair):
        action = 'buy'

        http = self.url + action + pair #where pair should be a string of currency pair (in format of '/btcusd/')

        res = request.post(http, param = {'key': self.key, 'signature': _sign(self, nonce), 'nonce': nonce, 'price': price, 'amount': amount, 'limit_price': limit_price})

    def postMarketExitOrder(self, nonce, price, amount, pair)
        action = 'sell'

        http = url + action + pair #where pair should be a string of currency pair (in format of '/btcusd/')

        res = request.post(http, param = {'key': self.key, 'signature': _sign(self, nonce), 'nonce': nonce, 'amount': amount}
        )

      def postLimitExitOrder(self, nonce, amount, limit_price, pair)
        action = 'sell/market'

        http = url + action + pair #where pair should be a string of currency pair (in format of '/btcusd/')

        res = request.post(http, param = {'key': self.key, 'signature': _sign(self, nonce), 'nonce': nonce, 'amount': amount, 'limit_price': limit_price}
        )

    def onTrade(self, pair, callback):
        assert callable(callback)
        self._bindSocket('live_trades_' + pair, 'trade', callback)


    def onOrderCreate(self, pair, callback):
        assert callable(callback)
        self._bindSocket('live_orders' + pair, 'order_created', callback)


    def _bindSocket(self, channel_name, event, callback):
        try:
            channel = self.pusher.subscribe(channel_name)
            channel.bind(event, callback)
        # @HANDLE Catch proper type of exception
        except:
            self.pusher.channels[channel_name].bind(event, callback)



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

        this_minute = [x[0] if x[2] > lookback_1 for x in self._ticks]
        prev_minute = [x[0] if x[2] < lookback_1 and x[2] > lookback_2 for x in self._ticks]

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

    timestamp_last = 0

    # _bars: List of (open, close, high, low, minute)
    # @only recording the stat of the previous minute
    # default bar size is 1 minute
    # max_lookback is number of bars to store
    def __init__(self, period=60, max_lookback=100):
        self._bars = []
        self._max_lookback = max_lookback

        self.period = period
        self.last = 0


    def update(self, price, timestamp=None):
        now = time.time()

        if timestamp == None:
            timestamp = time.time()

        if timestamp - timestamp_last >= 60 or timestamp % period  < timestamp_last % period:
            print("Updating...")

            ticks = []
            ticks.append(price, timestamp)

            ticks_last = []
            for tick in ticks:
                if tick[1] > (now - now%period) - period
                    tick_last.append(tick)
                tick = []

            self._min = min(item[0] for item in tick_last)
            self._max = max(item[1] for item in tick_last)
            self._open = min(item[0] for item in tick_last)
            self._close = max(item[1] for item in tick_last)

            self._bars.append[self._open, self._close, self._max, self._min, timestamp % self.period]

            self.close = self.last # the last 1 min close is the previous tick price
            self.last = price  # update the current tick prcie

            timestamp_last = timestamp

    def prune(): #discard the entries after 100 trades within one minute
        self._bars = self._bars[self.max_lookback:]



class Portfolio:

    def amount() # how much portfolio I have rn
    def update() #use to recalculate your liquidity AFTER A TRADE IS REALIZED


# @HARDCODE @REMOVE
five_min = MovingWindow(300, 'eth')
eight_min = MovingWindow(480, 'eth')
bar = CandleBar()

equity_at_risk: 0.1
timelag_required = 10
crossover_time = None

def update_candle(tick):
    tick = json.loads(tick)
    price = tick['price']
    timestamp = float(tick['timestamp'])

    bar.update(price, timestamp)


def trade_strategy(tick):
    tick = json.loads(tick)
    price = tick['price']
    volume = tick['amount']
    timestamp = float(tick['timestamp'])

    print("Some idiot traded ETH")

    five_min.update(price, volume, timestamp)
    eight_min.update(price, volume, timestamp)

    if #we have not entered the position:
        if five_min.avg > eight_min.avg :
            if crossover_time is None:
                crossover_time = time.time()
            elif time.time() - crossover_time >= 10:
                #buy in
                print("Lets buy that shit: @", price)
                crossover_time = None
        else :
            crossover_time = None

    else :
        if five_min.avg < eight_min.avg :
            if crossover_time is None:
                crossover_time = time.time()
            elif time.time() - crossover_time >= 10:
                #sell
                print("Lets sell that shit: @", price)
                portfolio.update()
                crossover_time = None
        else :
            crossover_time = None


def main():
    bs = BitstampFeed()
    bs.onTrade('ethusd', trade_strategy)
    bs.onTrade('ethusd', update_candle)

    while True:
        time.sleep(1)


if __name__ == '__main__':
    print('Hello crypto!')
    main()


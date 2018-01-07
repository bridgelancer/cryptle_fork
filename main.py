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


    def getTicker(self, pair, callback=None):
        return get('/ticker/' + pair, callback=callback)


    def getOrderbook(self, pair, callback=None):
        return get('/order_book/' + pair, callback=callback)


    def getBalance(self):
        assert self.secret is not None

        params = self._authParams()
        return get('/balance/', params=params)


    def getOrderStatus(self, order_id):
        assert self.secret is not None

        params = self._authParams()
        params['id'] = order_id
        return get('/order_status', params=params)


    def get(endpoint, callback=None, params=None):
        assert params is None or isinstance(params, dict)

        res = req.get(self.url + endpoint, pararms)
        c = res.status_code

        if c != 200:
            raise ConnectionError('Server returned error ' + str(c))

        parsed_res = json.loads(res.text)

        if callback == None:
            return parsed_res
        else:
            assert callable(callback)
            return callback(parsed_res)


    def _authParams(self):
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

    # _bars: List of (open, close, high, low)
    # default bar size is 1 minute
    # max_lookback is number of bars to store
    def __init__(self, period=60, max_lookback=100):
        self._bars = []
        self._max_lookback = max_lookback

        self.period = period
        self.last = 0


    def update(self, price, timestamp=None):
        if timestamp == None:
            timestamp = time.time()

        self.last = price


    def prune():
        self._bars = self.bars[self.max_lookback:]

class Portfolio:
    
    def amount() # how much portfolio I have rn
    def update() #use to recalculate your liquidity AFTER A TRADE IS REALIZED


# @HARDCODE @REMOVE
five_min = MovingWindow(300, 'eth')
eight_min = MovingWindow(480, 'eth')
equity_at_risk: 0.1
timelag_required = 10
crossover_time = None


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

    while True:
        time.sleep(1)


if __name__ == '__main__':
    print('Hello crypto!')
    main()


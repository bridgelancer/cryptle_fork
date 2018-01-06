import numpy as np
import pandas as pd
import requests as req
import json
import time

import pysher
import hmac
import hashlib

class Bitstamp:

    def __init__(self, key=None, secret=None, customer_id=None):
        self.key = key
        self.secret = secret
        self.id = customer_id

        api_key = 'de504dc5763aeef9ff52'
        pusher = pysher.Pusher(api_key)
        pusher.connect()
        time.sleep(2)

        self.pusher = pusher

    def get(endpoint, callback=None, params=None):
        url = 'https://www.bitstamp.net/api/v2'
        res = req.get(url + endpoint, pararms)
        c = res.status_code

        if c != 200:
            raise ConnectionError('Server returned error ' + str(c))

        parsed_res = json.loads(res.text)

        if callback == None:
            return parsed_res
        elif self._isCallback(callback):
            return callback(parsed_res)

    def getTicker(self, pair, callback=None):
        return get('/ticker/' + pair, callback=callback)

    def getOrderbook(self, pair, callback=None):
        return get('/order_book/' + pair, callback=callback)

    def getBalance(self):
        if (not self._hasSecret()):
            return get('/balance/', params={})

    def onTrade(self, pair, callback):
        self._isCallback(callback)
        self._bindSocket('live_trades_' + pair, 'trade', callback)

    def onOrderCreate(self, pair, callback):
        self._isCallback(callback)
        self._bindSocket('live_orders' + pair, 'order_created', callback)

    def _bindSocket(self, channel_name, event, callback):
        try:
            channel = self.pusher.subscribe(channel_name)
            channel.bind(event, callback)
        except:
            self.pusher.channels[channel_name].bind(event, callback)

    def _sign(self, nonce):
        message = nonce + self.id + self.key
        signature = hmac.new(
                self.secret,
                msg=message.encode('utf-8'),
                digestmod=hashlib.sha256
        ).hexdigest().upper()
        return signature

    def _hasSecret(self):
        return self.secret != None

    @staticmethod
    def _isCallback(callback):
        if not callable(callback):
            raise TypeError("Non-callable argument passed")
        return True


class MovingWindow:

    # Period is the number of seconds in the lookback window
    # Ticker (optional) is meta-info about what series is being tracked
    def __init__(self, period, ticker=None):
        self._ticks = [] # @OPTIMIZE use NumPy arrays


        self.avg = 0
        self.volume = 0
        self.dollar_volume = 0

        self.period = period
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
        lookback = now - self.period

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

five_min = MovingWindow(300, 'eth')

def trade_strategy(tick):
    tick = json.loads(tick)
    price = tick['price']
    volume = tick['amount']
    timestamp = float(tick['timestamp'])

    print("Some idiot traded ETH")

    five_min.update(price, volume, timestamp)
    if five_min.avg < price:
        print("Lets buy that shit: @", price)

def main():
    bs = Bitstamp()
    bs.onTrade('ethusd', trade_strategy)

    while True:
        time.sleep(1)

if __name__ == '__main__':
    print('Hello crypto!')
    main()


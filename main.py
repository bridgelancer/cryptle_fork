import numpy as np
import pandas as pd
import requests as req
import json
import time

import pysher
import hmac
import hashlib

def sign(nonce, customer_id, api_key, secret):
    message = nonce + customer_id + api_key
    signature = hmac.new(
            secret,
            msg=message.encode('utf-8'),
            digestmod=hashlib.sha256
    ).hexdigest().upper()
    return signature

class Bitstamp:

    def __init__(self, secret=None)
        self.secret = secret

        api_key = 'de504dc5763aeef9ff52'
        pusher = pysher.Pusher(api_key)
        pusher.connect()

    def get(endpoint, callback=None, params=None):
        url = 'https://www.bitstamp.net/api/v2'
        res = req.get(url + endpoint, pararms)
        c = res.status_code

        if c != 200:
            raise ConnectionError('Server returned error ' + str(c))

        parsed_res = json.loads(res.text)

        if callback == None:
            return parsed_res
        elif _isCallback(callback):
            return callback(parsed_res)

    def getTicker(self, pair, callback=None,):
        return get('/ticker/' + pair, callback)

    def getOrderbook(self, pair, callback=None,):
        return get('/order_book/' + pair, callback)

    def onTrade(self, pair, callback):
        _isCallback(callback)
        _bindSocket('live_trades_' + pair, 'trade' callback)

    def onOrderCreate(self, pair, callback):
        _isCallback(callback)
        _bindSocket('live_orders' + pair, 'order_created', callback)

    def _bindSocket(self, channel_name, event, callback)
        if pusher.channel(channel_name):
            channel = pusher.channel(channel_name)
        else:
            channel = pusher.subscribe(channel_name)

        channel.bind(event, callback)

    @staticmethod
    def _isCallback(callback):
        if !callable(callback):
            raise TypeError("Non-callable argument passed")
        return True


class PriceWindow:

    # Period is the number of seconds in the lookback window
    # Ticker (optional) is meta-info about what series is being tracked
    def __init__(self, period, ticker=None):
        self.ticks= []
        self.avg = 0
        self.high = 0
        self.low = 100000000000
        self.volume = 0
        self.dollar_volume = 0
        self.period = period
        self.ticker = ticker

    def __str__(self):
        return self.ticker

    def update(self, price, volume, timestamp=None):
        if self.high < price:
            self.high = price
        elif self.low > price:
            self.low = price

        if timestamp == None:
            timestamp = time.time()

        self.latest = price
        self.volume = self.volume + volume
        self.dollar_volume = self.dollar_volume + price * volume
        self.avg = self.dollar_volume / self.volume

        ticks.append((price, volume, timestamp))
        self.clear()

    def clear(self):
        now = time.time()
        lookback = now - self.period

        while True:
            if self.ticks[0][2] < lookback:
                tick = self.ticks.pop(0)
                self.volume = self.volume - tick[1]
                self.dollar_volume = self.dollar_volume - tick[0] * tick[1]
                self.avg = self.dollar_volume / self.volume
            else:
                break


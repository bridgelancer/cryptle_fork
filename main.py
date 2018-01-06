API_SECRET = ''
API_KEY = 'de504dc5763aeef9ff52'
BITSTAMP_URL = 'https://www.bitstamp.net/api/v2/'

import numpy as np
import pandas as pd
import requests as req
import json
import time

import pysher
import hmac
import hashlib

def sign(nonce, customer_id, api_key):
    message = nonce + customer_id + api_key
    signature = hmac.new(
            API_SECRET,
            msg=message.encode('utf-8'),
            digestmod=hashlib.sha256
    ).hexdigest().upper()
    return signature

def bitstamp_api(endpoint, callback=None, params=None):
    res = req.get(BITSTAMP_URL + endpoint, pararms)
    c = res.status_code

    if c != 200:
        raise ConnectionError('Server returned error ' + str(c))

    parsed_res = json.loads(res.text)

    if callback != None:
        return callback(parsed_res)
    else:
        return parsed_res

class Bitstamp:

    def __init__(self, secret=None)
        self.secret = secret
        pusher = pysher.Pusher(APP_KEY)
        pusher.connect()

    def onTrade(pair, callback):
        _checkCallback(callback)
        _bindSocket('live_trades_' + pair, 'trade' callback)

    def onOrderCreate(pair, callback):
        _checkCallback(callback)
        _bindSocket('live_orders' + pair, 'order_created', callback)

    def _bindSocket(channel_name, event, callback)
        if pusher.channel(channel_name):
            channel = pusher.channel(channel_name)
        else:
            channel = pusher.subscribe(channel_name)

        channel.bind(event, callback)

    def _checkCallback(callback):
        if !callable(callback):
            raise TypeError("Non-callable argument passed")


class PriceWindow:

    # Period is the number of seconds in the lookback window
    # Ticker (optional) is meta-info about what series is being tracked
    def __init__(self, period, ticker=None):
        self.ticks= []
        self.volume = 0
        self.avg = 0
        self.high = 0
        self.low = 100000000000
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

        new_vol = self.volume + volume
        self.avg = (self.volume * self.avg + price * volume) / new_vol
        self.volume = new_vol

        ticks.append((price, volume, timestamp))
        self.clear()

    def clear(self):
        now = time.time()
        lookback = now - self.period

        while True:
            if self.ticks[0][2] < lookback:
                self.ticks.pop(0)
            else:
                break

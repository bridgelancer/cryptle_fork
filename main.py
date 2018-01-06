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

def bitstamp_socket(channel, event, callback):
    pusher = pysher.Pusher(APP_KEY)
    pusher.connect()
    channel = pusher.subscribe(channel)
    channel.bind(event, callback)

def bitstamp_api(endpoint, callback=None, params=None):
    res = req.get(BITSTAMP_URL + endpoint, pararms)
    c = res.status_code

    if c != 200:
        raise ConnectionError('Server returned error ' + str(c))

    if callback != None:
        return callback(res)
    else:
        return res

class live_min_price:

    def __init__(self, ticker):
        self.ticks= []
        self.ticker = ticker
        self.volume = 0
        self.avg = 0
        self.high = 0
        self.low = 100000000

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
        i = self.ticks
        self.ticks = self.ticks[i:]

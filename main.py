API_SECRET = ''
API_KEY = 'de504dc5763aeef9ff52'
BITSTAMP_URL = 'https://www.bitstamp.net/api/v2/'

import numpy as np
import pandas as pd
import requests as req
import json
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

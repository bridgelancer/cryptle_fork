import hmac
import hashlib

API_SECRET = ''
API_KEY = 'de504dc5763aeef9ff52'

def sign(nonce, customer_id, api_key):
    message = nonce + customer_id + api_key
    signature = hmac.new(
            API_SECRET,
            msg=message.encode('utf-8'),
            digestmod=hashlib.sha256
    ).hexdigest().upper()
    return signature

import numpy as np
import pandas as pd
import requests as req
import json
import pysher


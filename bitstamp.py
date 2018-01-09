import logging
import time
import json
import hmac
import hashlib

import pysher
import requests as req


logger = logging.getLogger('Bitstamp')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(name)s: %(asctime)s [%(levelname)s] %(message)s', '%Y-%m-%d %H:%M:%S')


class BitstampREST:

    def __init__(self, key=None, secret=None, customer_id=None):
        self.key = key
        self.secret = secret
        self.id = customer_id
        self.url = 'https://www.bitstamp.net/api/v2'


    def getTicker(self, pair):
        assert isinstance(pair, str)
        return self._get('/ticker/' + pair)


    def getOrderbook(self, pair):
        assert isinstance(pair, str)
        return self._get('/order_book/' + pair)


    def getBalance(self, pair=''):
        if pair != '':
            pair += '/'

        params = self._authParams()
        return self._post('/balance/' + pair, params=params)


    def getOrderStatus(self, order_id):
        assert isinstance(order_id, int)

        params = self._authParams()
        params['id'] = order_id
        return self._post('/order_status/', params=params)


    def limitBuy(self, pair, amount, price):
        assert isinstance(pair, str)
        assert amount > 0
        assert price > 0

        params = self._authParams()
        params['amount'] = amount
        params['price'] = price

        res = self._post('/buy/' + pair + '/', params=params)

        handleBitstampErrors(res, 'Limit buy ' + pair + ' failed')
        return res


    def limitSell(self, pair, amount, price):
        assert isinstance(pair, str)
        assert amount > 0
        assert price > 0

        params = self._authParams()
        params['amount'] = amount
        params['price'] = price

        res = self._post('/sell/' + pair + '/', params=params)

        handleBitstampErrors(res, 'Limit sell ' + pair + ' failed')
        return res


    def marketBuy(self, pair, amount):
        assert isinstance(pair, str)
        assert amount > 0

        params = self._authParams()
        params['amount'] = amount

        res = self._post('/buy/market/' + pair + '/', params=params)

        handleBitstampErrors(res, 'Market buy ' + pair + ' failed')
        return res


    def marketSell(self, pair, amount):
        assert isinstance(pair, str)
        assert amount > 0

        params = self._authParams()
        params['amount'] = amount

        res = self._post('/sell/market/' + pair + '/', params=params)

        handleBitstampErrors(res, 'Market sell ' + pair + ' failed')
        return res


    def cancnelOrder(self, order_id):
        assert isinstance(order_id, int)

        params = self._authParams()
        params['id'] = price
        return self._post('/order_status/', params=parms)


    def _get(self, endpoint, params=None):
        assert isinstance(endpoint, str)
        assert isinstance(params, dict) or params is None

        handleConnectionErrors(res)
        parsed_res = json.loads(res.text)
        return parsed_res


    def _post(self, endpoint, params):
        assert isinstance(endpoint, str)
        assert isinstance(params, dict)

        res = req.post(self.url + endpoint, params)

        handleConnectionErrors(res)
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
        assert isinstance(pair, str)
        assert callable(callback)

        if pair == 'btcusd':
            self._bindSocket('live_trades', 'trade', callback)
        else:
            self._bindSocket('live_trades_' + pair, 'trade', callback)


    def onOrderCreate(self, pair, callback):
        assert isinstance(pair, str)
        assert callable(callback)

        if pair == 'btcusd':
            self._bindSocket('live_orders', 'order_created', callback)
        else:
            self._bindSocket('live_orders_' + pair, 'order_created', callback)


    def _bindSocket(self, channel_name, event, callback):

        if channel_name not in self.pusher.channels:
            self.pusher.subscribe(channel_name)

        channel = self.pusher.channels[channel_name]
        channel.bind(event, callback)



def handleConnectionErrors(res):
    c = res.status_code

    if c == 400:
        logger.error('400 Bad Request Error')
        logger.error(res.text)
        raise ConnectionError('Server 400 Bad Request Error')
    elif c == 401:
        logger.error('401 Unauthorized Error')
        logger.error(res.text)
        raise ConnectionError('Server 401 Unauthorized Error')
    elif c == 403:
        logger.error('403 Bad Request Error')
        logger.error(res.text)
        raise ConnectionError('Server 403 Forbidden')
    elif c == 404:
        logger.error('404 Page Not Found')
    elif c != 200:
        logger.error(res.text)
        raise ConnectionError('Server returned error ' + str(c))



def handleBitstampErrors(res, message):
    if res['status'] == 'error':
        raise RuntimeWarning(message)


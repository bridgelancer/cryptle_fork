from .utility import *

from time import time as now
import hashlib
import hmac
import json
import requests as req
import logging
log = logging.getLogger(__name__)


class Bitstamp:
    url = 'https://www.bitstamp.net/api/v2'

    def __init__(self, key=None, secret=None, customer_id=None):
        self.key = key
        self.secret = secret
        self.id = customer_id


    # [Application level interface]
    def getTicker(self, pair):
        checkType(pair, str)
        return self._get('/ticker/' + pair)


    def getOrderbook(self, pair):
        checkType(pair, str)
        return self._get('/order_book/' + pair)


    def getBalance(self, pair=''):
        if pair != '':
            pair += '/'

        return self._post('/balance/' + pair)


    def getOrderStatus(self, order_id):
        checkType(order_id, int)

        res = self._post('/order_status/', params={'id': order_id})
        self.handleBitstampErrors(res, 'Open order query failed')
        return res


    def getOpenOrders(self, pair='all/'):
        res = self_post('/open_orders/' + pair)
        self.handleBitstampErrors(res, 'Open orders query failed')
        return res


    def marketBuy(self, pair, amount):
        '''Place marketbuy on bitstamp. Returns python dict when order terminates'''
        checkType(amount, int, float)
        assert amount > 0

        res = self._post('/buy/market/' + pair + '/', params={'amount': truncate(amount, 8)})
        res['timestamp'] = now()

        self.handleBitstampErrors(res, 'Market buy {} failed'.format(pair.upper()))
        return res


    def marketSell(self, pair, amount):
        '''Place marketsell on bitstamp. Returns python dict when order terminates'''
        checkType(amount, int, float)
        assert amount > 0

        res = self._post('/sell/market/' + pair + '/', params={'amount': truncate(amount, 8)})
        res['timestamp'] = now()

        self.handleBitstampErrors(res, 'Market sell {} failed'.format(pair.upper()))
        return res


    def limitBuy(self, pair, amount, price):
        '''Place limitbuy on bitstamp. Returns python dict when order terminates

        Note:
            This method is not fully implemented yet
        '''
        checkType(amount, int, float)
        checkType(price, int, float)
        assert amount > 0
        assert price > 0

        params = {}
        params['amount'] = truncate(amount, 8)
        params['price'] = truncate(price)

        res = self._post('/buy/' + pair + '/', params=params)
        res['timestamp'] = now()

        self.handleBitstampErrors(res, 'Limit buy {} failed'.format(pair.upper()))
        return res


    def limitSell(self, pair, amount, price):
        '''Place limitsell on bitstamp. Returns python dict when order terminates

        Note:
            This method is not fully implemented yet
        '''
        checkType(amount, int, float)
        checkType(price, int, float)
        assert amount > 0
        assert price > 0

        params = {}
        params['amount'] = truncate(amount, 8)
        params['price'] = truncate(price)

        res = self._post('/sell/' + pair + '/', params=params)
        res['timestamp'] = now()

        self.handleBitstampErrors(res, 'Limit sell {} failed'.format(pair.upper()))
        return res


    def cancnelOrder(self, order_id):
        '''Cancel an open limit order'''
        checkType(order_id, int)
        return self._post('/cancel_order/', params={'id': order_id})


    def cancnelAllOrder(self):
        return self._post('/cancel_all_orders/')


    # [Low level requests interfae]
    def _get(self, endpoint, params=None):
        '''Send GET request to bitstamp. Returns python dictionary.'''
        checkType(endpoint, str)
        checkType(params, dict, type(None))

        try:
            res = req.get(self.url + endpoint, params)
            self.handleConnectionErrors(res)
        except ConnectionError:
            return {'status': 'error', 'reason': 'ConnectionError'}

        res = json.loads(res.text)
        return res


    def _post(self, endpoint, params=None):
        '''Send POST request to bitstamp. Returns python dictionary.'''
        checkType(endpoint, str)
        checkType(params, dict, type(None))

        params = params or {}
        params = {**self._authParams(), **params}

        try:
            res = req.post(self.url + endpoint, params)
            self.handleConnectionErrors(res)
        except ConnectionError:
            return {'status': 'error', 'reason': 'ConnectionError'}

        res = json.loads(res.text)
        return res


    def _authParams(self):
        assert self.secret is not None

        nonce = int(now() * 100)
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


    @staticmethod
    def handleConnectionErrors(res):
        c = res.status_code

        if c == 400:
            log.error('Bitstamp: 400 Bad Request Error')
            log.error(res.text)
            raise ConnectionError
        elif c == 401:
            log.error('Bitstamp: 401 Unauthorized Error')
            log.error(res.text)
            raise ConnectionError
        elif c == 403:
            log.error('Bitstamp: 403 Bad Request Error')
            log.error(res.text)
            raise ConnectionError
        elif c == 404:
            log.error('Bitstamp: 404 Page Not Found')
            raise ConnectionError
        elif c != 200:
            log.error('Bitstamp: Error {}'.format(c))
            log.error(res.text)
            raise ConnectionError


    @staticmethod
    def handleBitstampErrors(res, message):
        if 'status' not in res:
            res['status'] = 'success'
            return

        if res['status'] == 'error':
            log.error(message + ': ' + str(res['reason']))
            res['price'] = 0
            res['amount'] = 0

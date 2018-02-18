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
    def getTicker(self, *, asset, base_currency):
        endpoint = '/ticker/'
        return self._get(endpoint + self._encode_pair(asset, base_currency))


    def getOrderbook(self, *, asset, base_currency):
        endpoint = '/order_book/'
        return self._get(endpoint + self._encode_pair(asset, base_currency))


    # @Hardcode: base_currecy
    def getBalance(self, *, asset='', base_currency=''):
        '''Request account balance from bitstamp.

        Args:
            asset (str): Optional argument to request only part of the balance
                related to the specified pair.
            base_currency (str):

        Returns:
            The full balance, keyed by asset names
        '''
        balance = self._post('/balance/' + self._encode_pair(asset, base_currency))
        return self._decode_balance(balance)


    def getOrderStatus(self, *, order_id):
        checkType(order_id, int)

        res = self._post('/order_status/', params={'id': order_id})
        self.handleBitstampErrors(res, 'Open order query failed')
        return res


    def getOpenOrders(self, *, asset='all/', base_currency='usd'):
        res = self_post('/open_orders/' + self._encode_pair(asset, base_currency))
        self.handleBitstampErrors(res, 'Open orders query failed')
        return res


    def marketBuy(self, *, asset, currency, amount):
        '''Place marketbuy on bitstamp. Returns python dict when order terminates'''
        checkType(amount, int, float)
        assert amount > 0

        params = {
            'amount': truncate(amount, 8)
        }

        endpoint = '/buy/market/'
        res = self._post(endpoint + self._encode_pair(asset, currency), params=params)
        res['timestamp'] = now()

        self.handleBitstampErrors(res, 'Market buy {} failed'.format(pair[0].upper()))
        return res


    def marketSell(self, *, asset, currency, amount):
        '''Place marketsell on bitstamp. Returns python dict when order terminates'''
        checkType(amount, int, float)
        assert amount > 0

        params = {
            'amount': truncate(amount, 8)
        }

        endpoint = '/sell/market/'
        res = self._post(endpoint + self._encode_pair(asset, currency), params=params)
        res['timestamp'] = now()

        self.handleBitstampErrors(res, 'Market sell {} failed'.format(pair[0].upper()))
        return res


    def limitBuy(self, *, asset, currency, amount, price):
        '''Place limitbuy on bitstamp. Returns python dict when order terminates

        Note:
            This method is not fully implemented yet
        '''
        checkType(amount, int, float)
        checkType(price, int, float)
        assert amount > 0
        assert price > 0

        params = {
            'amount': truncate(amount, 8),
            'price': truncate(price, 8)
        }

        endpoint = '/buy/'
        res = self._post(endpoint + self._encode_pair(asset, currency), params=params)
        res['timestamp'] = now()

        self.handleBitstampErrors(res, 'Limit buy {} failed'.format(pair[0].upper()))
        return res


    def limitSell(self, *, asset, currency, amount, price):
        '''Place limitsell on bitstamp. Returns python dict when order terminates

        Note:
            This method is not fully implemented yet
        '''
        checkType(amount, int, float)
        checkType(price, int, float)
        assert amount > 0
        assert price > 0

        params = {
            'amount': truncate(amount, 8),
            'price': truncate(price, 8)
        }

        endpoint = '/sell/'
        res = self._post(endpoint + self._encode_pair(asset, currency), params=params)
        res['timestamp'] = now()

        self.handleBitstampErrors(res, 'Limit sell {} failed'.format(pair[0].upper()))
        return res


    def cancnelOrder(self, order_id):
        '''Cancel an open limit order'''
        checkType(order_id, int)
        return self._post('/cancel_order/', params={'id': order_id})


    def cancnelAllOrder(self):
        return self._post('/cancel_all_orders/')


    # [Low level requests interfae]
    def _get(self, endpoint):
        '''Send GET request to bitstamp. Return python dict.'''
        checkType(endpoint, str)

        url = self.url + endpoint

        try:
            log.debug('Sending GET request: ' + url)
            res = req.get(url)
            self.handleConnectionErrors(res)
        except ConnectionError:
            return {'status': 'error', 'reason': 'ConnectionError'}

        res = json.loads(res.text)
        return res


    def _post(self, endpoint, params=None):
        '''Send POST request to bitstamp. Return python dict.'''
        checkType(endpoint, str)
        checkType(params, dict, type(None))

        params = params or {}
        params = {**self._authParams(), **params}

        url = self.url + endpoint

        try:
            log.debug('Sending POST request: ' + url)
            res = req.post(url, params)
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
    def _encode_pair(asset, base_currency):
        '''Format a traded asset/base_currency pair into bitstamp representation'''
        return asset + base_currency


    @staticmethod
    def _decode_balance(balance):
        '''Format balance entries in the json loaded python dict'''
        # @Hardcode: For optimization
        return {
            k[:3]: float(v) for k, v in balance.items() if k.endswith('available') and float(v) > 1e-8
        }


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


    # @Fix
    @staticmethod
    def handleBitstampErrors(res, message):
        if 'status' not in res:
            res['status'] = 'success'
            return

        if res['status'] == 'error':
            log.error(message + ': ' + str(res['reason']))
            res['price'] = 0
            res['amount'] = 0

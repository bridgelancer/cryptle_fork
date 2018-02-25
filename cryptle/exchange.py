import hashlib
import hmac
import logging
import json
from time import time as now

import requests as req


log = logging.getLogger(__name__)


class ExchangeError(Exception):
    pass


class OrderError(ExchangeError):
    pass


def logHTTPError(res):
    '''
    Args:
        res: Response object from requests
    '''
    if code == 400:
        msg = '400 Bad Request'
    elif code == 401:
        msg = '401 Unauthorized Request'
    elif code == 403:
        msg = '403 Forbidden Request'
    elif code == 404:
        msg = '404 Page Not Found'
    elif code == 500:
        msg = '500 Internal Server Error'
    else:
        msg = '{} Error'.format(code)

    log.error(msg + '\n' + res.text)


class Bitstamp:

    url = 'https://www.bitstamp.net/api/v2'

    def __init__(self, key=None, secret=None, customer_id=None):
        self.key = key
        self.secret = secret
        self.id = customer_id


    # [Public Functions]
    def getTicker(self, asset, base_currency):
        endpoint = '/ticker/'
        return self._get(endpoint + self._encode_pair(asset, base_currency))


    def getOrderbook(self, asset, base_currency):
        endpoint = '/order_book/'
        return self._get(endpoint + self._encode_pair(asset, base_currency))


    # [Private Functions]
    def getBalance(self, asset='', base_currency=''):
        '''Request account balance from bitstamp.

        Args:
            asset (str): Optional argument to request only part of the balance
                related to the specified pair.
            base_currency (str):

        Returns:
            The full balance, keyed by asset names

        Raises:
            ConnectionError: For non 200 HTTP status code, raised by _post()
        '''
        res = self._post('/balance/' + self._encode_pair(asset, base_currency))

        if self.hasBitstampError(res):
            log.error('Balance request failed')
            raise ExchangeError

        return self._decode_balance(res)


    def getOrderStatus(self, order_id):
        res = self._post('/order_status/', params={'id': order_id})

        if self.hasBitstampError(res):
            log.error('Open orders request failed')
            raise ExchangeError

        return res


    def getOpenOrders(self, asset='all/', base_currency='usd'):
        res = self_post('/open_orders/' + self._encode_pair(asset, base_currency))

        if self.hasBitstampError(res):
            log.error('Open orders request failed')
            raise ExchangeError

        return res


    def sendMarketBuy(self, asset, currency, amount):
        '''Place marketbuy on bitstamp. Returns python dict when order terminates.

        Args:
            asset: Name of asset to buy
            currency: Base currency to be used for the transaction
            amount: Number of assets to buy

        Raises:
            ConnectionError: For non 200 HTTP status code, raised by _post()
            OrderError: If bitsatmp respone contains {'status': error}
        '''
        params = {
            'amount': _truncate(amount, 8)
        }

        endpoint = '/buy/market/'
        res = self._post(endpoint + self._encode_pair(asset, currency), params=params)

        if self.hasBitstampError(res):
            log.error('Market buy {} failed: {}'.format(asset.upper(), res['reason']))
            raise OrderError

        res['timestamp'] = now()
        return res


    def sendMarketSell(self, asset, currency, amount):
        '''Place marketsell on bitstamp. Returns python dict when order terminates

        Args:
            asset: Name of asset to sell
            currency: Base currency to be gained from this transaction
            amount: Number of assets to sell

        Raises:
            ConnectionError: For non 200 HTTP status code, raised by _post()
            OrderError: If bitsatmp respone contains {'status': error}
        '''
        params = {
            'amount': _truncate(amount, 8)
        }

        endpoint = '/sell/market/'
        res = self._post(endpoint + self._encode_pair(asset, currency), params=params)

        if self.hasBitstampError(res):
            log.error('Market sell {} failed: {}'.format(asset.upper(), res['reason']))
            raise OrderError

        res['timestamp'] = now()
        return res


    def sendLimitBuy(self, asset, currency, amount, price):
        '''Place limitbuy on bitstamp. Returns python dict when order terminates

        Args:
            asset: Name of asset to buy
            currency: Base currency to be used for the transaction
            amount: Number of assets to buy
            price: Price (in base currency) for the order to be placed

        Raises:
            ConnectionError: For non 200 HTTP status code, raised by _post()
            OrderError: If bitsatmp respone contains {'status': error}

        Note:
            This method is not fully implemented yet. A proper version should either be
            async, or returns the ordreId.
        '''
        params = {
            'amount': _truncate(amount, 8),
            'price': _truncate(price, 8)
        }

        endpoint = '/buy/'
        res = self._post(endpoint + self._encode_pair(asset, currency), params=params)

        if self.hasBitstampError(res):
            log.error('Limit buy {} failed: {}'.format(asset.upper(), res['reason']))
            raise OrderError

        res['timestamp'] = now()
        return res


    def sendLimitSell(self, asset, currency, amount, price):
        '''Place limitsell on bitstamp. Returns python dict when order terminates

        Args:
            asset: Name of asset to buy
            currency: Base currency to be used for the transaction
            amount: Number of assets to buy
            price: Price (in base currency) for the order to be placed

        Raises:
            ConnectionError: For non 200 HTTP status code, raised by _post()
            OrderError: If bitsatmp respone contains {'status': error}

        Note:
            This method is not fully implemented yet. A proper version should either be
            async, or returns the ordreId.
        '''
        params = {
            'amount': _truncate(amount, 8),
            'price': _truncate(price, 8)
        }

        endpoint = '/sell/'
        res = self._post(endpoint + self._encode_pair(asset, currency), params=params)

        if self.hasBitstampError(res):
            log.error('Limit sell {} failed: {}'.format(asset.upper(), res['reason']))
            raise OrderError

        res['timestamp'] = now()
        return res

    # @Document
    def sendOrderCancel(self, order_id):
        '''Cancel an open limit order'''
        return self._post('/cancel_order/', params={'id': order_id})


    # @Document
    def cancnelAllOrder(self):
        return self._post('/cancel_all_orders/')


    # [Low level requests interfae]
    def _get(self, endpoint):
        '''Send GET request to bitstamp. Return python dict.'''

        url = self.url + endpoint

        log.debug('Sending GET request: ' + url)
        res = req.get(url)

        if res.status_code // 100 != 2:
            logHTTPError(res)
            raise ConnectionError

        res = json.loads(res.text)
        return res


    def _post(self, endpoint, params=None):
        '''Send POST request to bitstamp. Return python dict.'''

        params = params or {}
        params = {**self._authParams(), **params}
        url = self.url + endpoint

        log.debug('Sending POST request: ' + url)
        res = req.post(url, params)

        if res.status_code // 100 != 2:
            logHTTPError(res)
            raise ConnectionError

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
    def hasBitstampError(res):
        try:
            return res['status'] == 'error'
        except KeyError:
            pass


def _truncate(f, dp):
    fmt = '{:.' + str(dp) + 'f}'
    s = fmt.format(f)
    return float(s)

import logging
import time
import json
import hmac
import hashlib

import pysher
import requests as req


log = logging.getLogger('Exchange')


class PaperExchange:

    def __init__(self):
        self.price = 0
        self.timestamp = 0


    def marketBuy(self, pair, amount):
        assert isinstance(pair, str)
        assert amount > 0

        log.info('Buy  {:7.5g} {} @${:.2g}'.format(amount, pair.upper(), self.price))
        return {'price': self.price, 'amount': amount}


    def marketSell(self, pair, amount):
        assert isinstance(pair, str)
        assert amount > 0

        log.info('Sell {:7.5g} {} @${:.2g}'.format(amount, pair.upper(), self.price))
        return {'price': self.price, 'amount': amount}


    def limitBuy(self, pair, amount, price):
        assert isinstance(pair, str)
        assert amount > 0
        assert price > 0

        log.info('Buy  {:7.5g} {} @${:.2g}'.format(amount, pair.upper(), price))
        return {'price': price, 'amount': amount}


    def limitSell(self, pair, amount, price):
        assert isinstance(pair, str)
        assert amount > 0
        assert price > 0

        log.info('Sell {:7.5g} {} @${:.2g}'.format(amount, pair.upper(), price))
        return {'price': price, 'amount': amount}



class Bitstamp:

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

        self.handleBitstampErrors(res, 'Limit buy ' + pair.upper() + ' failed')
        return res


    def limitSell(self, pair, amount, price):
        assert isinstance(pair, str)
        assert amount > 0
        assert price > 0

        params = self._authParams()
        params['amount'] = amount
        params['price'] = price

        res = self._post('/sell/' + pair + '/', params=params)

        self.handleBitstampErrors(res, 'Limit sell ' + pair.upper() + ' failed')
        return res


    def marketBuy(self, pair, amount):
        assert isinstance(pair, str)
        assert amount > 0

        params = self._authParams()
        params['amount'] = amount

        res = self._post('/buy/market/' + pair + '/', params=params)

        self.handleBitstampErrors(res, 'Market buy ' + pair + ' failed')
        return res


    def marketSell(self, pair, amount):
        assert isinstance(pair, str)
        assert amount > 0

        params = self._authParams()
        params['amount'] = amount

        res = self._post('/sell/market/' + pair + '/', params=params)

        self.handleBitstampErrors(res, 'Market sell ' + pair + ' failed')
        return res


    def cancnelOrder(self, order_id):
        assert isinstance(order_id, int)

        params = self._authParams()
        params['id'] = price
        return self._post('/order_status/', params=parms)


    def _get(self, endpoint, params=None):
        assert isinstance(endpoint, str)
        assert isinstance(params, dict) or params is None

        res = req.post(self.url + endpoint, params)

        self.handleConnectionErrors(res)
        parsed_res = json.loads(res.text)
        return parsed_res


    def _post(self, endpoint, params):
        assert isinstance(endpoint, str)
        assert isinstance(params, dict)

        res = req.post(self.url + endpoint, params)

        self.handleConnectionErrors(res)
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


    @staticmethod
    def handleConnectionErrors(res):
        c = res.status_code

        if c == 400:
            log.error('400 Bad Request Error')
            log.error(res.text)
            raise ConnectionError('Server 400 Bad Request Error')
        elif c == 401:
            log.error('401 Unauthorized Error')
            log.error(res.text)
            raise ConnectionError('Server 401 Unauthorized Error')
        elif c == 403:
            log.error('403 Bad Request Error')
            log.error(res.text)
            raise ConnectionError('Server 403 Forbidden')
        elif c == 404:
            log.error('404 Page Not Found')
        elif c != 200:
            log.error(res.text)
            raise ConnectionError('Server returned error ' + str(c))


    @staticmethod
    def handleBitstampErrors(res, message):
        if 'status' not in res:
            return

        if res['status'] == 'error':
            log.error(message + ': ' + str(res['reason']))


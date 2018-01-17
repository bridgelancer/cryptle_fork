import hashlib
import hmac
import json
import logging
import time

import pysher
import requests as req


log = logging.getLogger('Exchange')


def truncate(f, dp):
    fmt = '{:.' + str(dp) + 'f}'
    s = fmt.format(f)
    return float(s)


def checkType(param, *types):
    valid_type = False

    for t in types:
        valid_type |= isinstance(param, t)

    if not valid_type:
        caller = inspect.stack()[1][3]
        passed = type(param).__name__

        fmt = "{} was passed to {}() where {} is expected"
        msg = fmt.format(passed, caller, types)

        raise TypeError(msg)


class PaperExchange:

    def __init__(self, commission=0, slippage=0):
        self.price = 0
        self.timestamp = 0
        self.commission = commission
        self.slippage = slippage


    def marketBuy(self, pair, amount):
        checkType(pair, str)
        checkType(amount, int, float)
        assert amount > 0

        price = self.price
        price *= (1 + self.commission)
        price *= (1 + self.slippage)

        log.info('Buy  {:7.5g} {} @${:.5g}'.format(amount, pair.upper(), price))
        log.info('Paid {:.5g} commission'.format(self.price * self.commission))
        return {'price': price, 'amount': amount, 'status': 'success'}


    def marketSell(self, pair, amount):
        checkType(pair, str)
        checkType(amount, int, float)
        assert amount > 0

        price = self.price
        price *= (1 - self.commission)
        price *= (1 - self.slippage)

        log.info('Sell {:7.5g} {} @${:.5g}'.format(amount, pair.upper(), self.price))
        log.info('Paid {:.5g} commission'.format(self.price * self.commission))
        return {'price': price, 'amount': amount, 'status': 'success'}


    def limitBuy(self, pair, amount, price):
        checkType(pair, str)
        checkType(amount, int, float)
        checkType(price, int, float)
        assert amount > 0
        assert price > 0

        price0 = price
        price *= (1 + self.commission)
        price *= (1 + self.slippage)

        log.info('Buy  {:7.5g} {} @${:.5g}'.format(amount, pair.upper(), price))
        log.info('Paid {:.5g} commission'.format(price0 * self.commission))
        return {'price': price, 'amount': amount, 'status': 'success'}


    def limitSell(self, pair, amount, price):
        checkType(pair, str)
        checkType(amount, int, float)
        checkType(price, int, float)
        assert amount > 0
        assert price > 0

        price0 = price
        price *= (1 - self.commission)
        price *= (1 - self.slippage)

        log.info('Sell {:7.5g} {} @${:.5g}'.format(amount, pair.upper(), price))
        log.info('Paid {:.5g} commission'.format(price0 * self.commission))
        return {'price': price, 'amount': amount, 'status': 'success'}



class Bitstamp:

    def __init__(self, key=None, secret=None, customer_id=None):
        self.key = key
        self.secret = secret
        self.id = customer_id
        self.url = 'https://www.bitstamp.net/api/v2'


    def getTicker(self, pair):
        checkType(pair, str)
        return self._get('/ticker/' + pair)


    def getOrderbook(self, pair):
        checkType(pair, str)
        return self._get('/order_book/' + pair)


    def getBalance(self, pair=''):
        if pair != '':
            pair += '/'

        params = self._authParams()
        return self._post('/balance/' + pair, params=params)


    def getOrderStatus(self, order_id):
        checkType(order_id, int)

        params = self._authParams()
        params['id'] = order_id

        res = self._post('/order_status/', params=params)
        self.handleBitstampErrors(res, 'Open order query failed')
        return res


    def getOpenOrders(self, pair='all/'):
        checkType(pair, str)

        params = self._authParams()

        res = self_post('/open_orders/' + pair, params=params)
        self.handleBitstampErrors(res, 'Open orders query failed')
        return res


    def marketBuy(self, pair, amount):
        checkType(pair, str)
        checkType(amount, int, float)
        assert amount > 0

        params = self._authParams()
        params['amount'] = truncate(amount, 8)

        res = self._post('/buy/market/' + pair + '/', params=params)

        self.handleBitstampErrors(res, 'Market buy {} failed'.format(pair.upper()))
        return res


    def marketSell(self, pair, amount):
        checkType(pair, str)
        checkType(amount, int, float)
        assert amount > 0

        params = self._authParams()
        params['amount'] = truncate(amount, 8)

        res = self._post('/sell/market/' + pair + '/', params=params)

        self.handleBitstampErrors(res, 'Market sell {} failed'.format(pair.upper()))
        return res


    def limitBuy(self, pair, amount, price):
        checkType(pair, str)
        checkType(amount, int, float)
        checkType(price, int, float)
        assert amount > 0
        assert price > 0

        params = self._authParams()
        params['amount'] = truncate(amount, 8)
        params['price'] = truncate(price)

        res = self._post('/buy/' + pair + '/', params=params)

        self.handleBitstampErrors(res, 'Limit buy {} failed'.format(pair.upper()))
        return res


    def limitSell(self, pair, amount, price):
        checkType(pair, str)
        checkType(amount, int, float)
        checkType(price, int, float)
        assert amount > 0
        assert price > 0

        params = self._authParams()
        params['amount'] = truncate(amount, 8)
        params['price'] = truncate(price)

        res = self._post('/sell/' + pair + '/', params=params)

        self.handleBitstampErrors(res, 'Limit sell {} failed'.format(pair.upper()))
        return res


    def cancnelOrder(self, order_id):
        checkType(order_id, int)

        params = self._authParams()
        params['id'] = price
        return self._post('/cancel_order/', params=parms)


    def cancnelAllOrder(self):
        params = self._authParams()
        return self._post('/cancel_all_orders/', params=parms)


    def _get(self, endpoint, params=None):
        checkType(endpoint, str)
        checkType(params, dict, type(None))

        try:
            res = req.post(self.url + endpoint, params)
            self.handleConnectionErrors(res)
        except ConnectionError:
            return {'status': 'error', 'reason': 'ConnectionError'}

        res = json.loads(res.text)
        return res


    def _post(self, endpoint, params):
        checkType(endpoint, str)
        checkType(params, dict)

        try:
            res = req.post(self.url + endpoint, params)
            self.handleConnectionErrors(res)
        except ConnectionError:
            return {'status': 'error', 'reason': 'ConnectionError'}

        res = json.loads(res.text)
        return res


    def _authParams(self):
        assert self.secret is not None

        nonce = int(time.time() * 100)
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


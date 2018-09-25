import hmac
import json
import hashlib
import logging
from time import sleep, time as now
from threading import Thread

import requests as req

from .exception import ExchangeError, OrderError


_LOG = logging.getLogger(__name__)


try:
    import cryptle.event as event
except ImportError as e:
    _LOG.error('{}', e)


def _log_http_error(res):
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

    _LOG.error(msg + '\n' + res.text)


def encode_pair(asset, base_currency):
    """Format a traded asset/base_currency pair into bitstamp representation"""
    return asset + base_currency


def decode_balance(balance):
    """Format balance entries in the json loaded python dict"""
    # @Hardcode: For optimization
    return {
        k[:3]: float(v) for k, v in balance.items() if k.endswith('available') and float(v) > 1e-8
    }


class Bitstamp:
    """REST API wrapper for Bitstamp.

    Args:
        key: Account key (subaccount)
        secret: Secret key (subaccount)
        customer_id: Customer ID (account)

    Note:
        Methods for placing orders with names starting with send*() are
        deprecated, but maintained for backwards-compatibility reasons.
    """
    url = 'https://www.bitstamp.net/api/v2'

    def __init__(self, key=None, secret=None, customer_id=None):
        self.key = key
        self.secret = secret
        self.id = customer_id

        self.poll_rate = 5
        self.polling = False
        self._polling_thread = None
        self._open_orders = set()

    # ----------
    # Public Functions (Mapping of API call)
    # ----------
    def getTicker(self, asset, base_currency):
        """Get ticker snapshot."""
        endpoint = '/ticker/'
        return self._public(endpoint + encode_pair(asset, base_currency))

    def getOrderbook(self, asset, base_currency):
        """Get orderbook snapshot."""
        endpoint = '/order_book/'
        return self._public(endpoint + encode_pair(asset, base_currency))

    # ----------
    # Private Functions
    # ----------
    def getBalance(self, asset='', base_currency=''):
        """Get account balance from bitstamp.

        Args:
            asset (str): Optional argument to request only part of the balance
                related to the specified pair.
            base_currency (str):

        Returns:
            The full balance, keyed by asset names

        Raises:
            ConnectionError: For non 200 HTTP status code, raised by _private()
        """
        res = self._private('/balance/' + encode_pair(asset, base_currency))

        if self.hasBitstampError(res):
            _LOG.error('Balance request failed')
            raise ExchangeError

        return decode_balance(res)

    def getOrderStatus(self, order_id):
        res = self._private('/order_status/', params={'id': order_id})

        if self.hasBitstampError(res):
            _LOG.error('Open orders request failed')
            raise ExchangeError

        return res

    def getOpenOrders(self, asset='all/', base_currency='usd'):
        res = self_private('/open_orders/' + encode_pair(asset, base_currency))

        if self.hasBitstampError(res):
            _LOG.error('Open orders request failed')
            raise ExchangeError

        return res

    def sendMarketBuy(self, *args, **kwargs):
        self.marketBuy(*args, **kwargs)

    def sendMarketSell(self, *args, **kwargs):
        self.marketSell(*args, **kwargs)

    def sendLimitBuy(self, *args, **kwargs):
        self.limitBuy(*args, **kwargs)

    def sendLimitSell(self, *args, **kwargs):
        self.limitSell(*args, **kwargs)

    def sendOrderCancel(self, *args, **kwargs):
        self.cancelOrder(*args, **kwargs)

    def marketBuy(self, asset, currency, amount):
        """Place marketbuy on bitstamp. Returns python dict when order terminates.

        Args:
            asset: Name of asset to buy
            currency: Base currency to be used for the transaction
            amount: Number of assets to buy

        Raises:
            ConnectionError: For non 200 HTTP status code, raised by _private()
            OrderError: If bitsatmp respone contains {'status': error}
        """
        params = {
            'amount': _truncate(amount, 8)
        }

        endpoint = '/buy/market/'
        res = self._private(endpoint + encode_pair(asset, currency), params=params)

        if self.hasBitstampError(res):
            _LOG.error('Market buy {} failed: {}'.format(asset.upper(), res['reason']))
            raise OrderError

        res['timestamp'] = now()
        return res

    def marketSell(self, asset, currency, amount):
        """Place marketsell on bitstamp. Returns python dict when order terminates

        Args:
            asset: Name of asset to sell
            currency: Base currency to be gained from this transaction
            amount: Number of assets to sell

        Raises:
            ConnectionError: For non 200 HTTP status code, raised by _private()
            OrderError: If bitsatmp respone contains {'status': error}
        """
        params = {
            'amount': _truncate(amount, 8)
        }

        endpoint = '/sell/market/'
        res = self._private(endpoint + encode_pair(asset, currency), params=params)

        if self.hasBitstampError(res):
            _LOG.error('Market sell {} failed: {}'.format(asset.upper(), res['reason']))
            raise OrderError

        res['timestamp'] = now()
        return res

    def limitBuy(self, asset, currency, amount, price):
        """Place limitbuy on bitstamp. Returns python dict when order terminates

        Args:
            asset: Name of asset to buy
            currency: Base currency to be used for the transaction
            amount: Number of assets to buy
            price: Price (in base currency) for the order to be placed

        Raises:
            ConnectionError: For non 200 HTTP status code, raised by _private()
            OrderError: If bitsatmp respone contains {'status': error}

        Note:
            This method is not fully implemented yet. A proper version should either be
            async, or returns the ordreId.
        """
        params = {
            'amount': _truncate(amount, 8),
            'price': _truncate(price, 8)
        }

        endpoint = '/buy/'
        res = self._private(endpoint + encode_pair(asset, currency), params=params)

        if self.hasBitstampError(res):
            _LOG.error('Limit buy {} failed: {}'.format(asset.upper(), res['reason']))
            raise OrderError

        res['timestamp'] = now()
        self._open_orders.add(res['id'])
        return res

    def limitSell(self, asset, currency, amount, price):
        """Place limitsell on bitstamp. Returns python dict when order terminates

        Args:
            asset: Name of asset to buy
            currency: Base currency to be used for the transaction
            amount: Number of assets to buy
            price: Price (in base currency) for the order to be placed

        Raises:
            ConnectionError: For HTTP non 200 status code
            OrderError: If bitsatmp respone contains {'status': error}

        Note:
            This method is not fully implemented yet. A proper version should either be
            async, or returns the ordreId.
        """
        params = {
            'amount': _truncate(amount, 8),
            'price': _truncate(price, 8)
        }

        endpoint = '/sell/'
        res = self._private(endpoint + encode_pair(asset, currency), params=params)

        if self.hasBitstampError(res):
            _LOG.error('Limit sell {} failed: {}'.format(asset.upper(), res['reason']))
            raise OrderError

        res['timestamp'] = now()
        self._open_orders.add(res['id'])
        return res

    def cancelOrder(self, order_id):
        """Cancel an open limit order."""
        self._open_orders.add(res['id'])
        return self._private('/cancel_order/', params={'id': order_id})

    def cancnelAllOrder(self):
        """Cancel all open order."""
        return self._private('/cancel_all_orders/')

    def orderStatus(self, oid):
        """Return the status of the provided limit order."""
        return self._private('/order_status/', params={'id': oid})

    def poll(self):
        if not self.key or not self.secret or not self.id:
            raise ValueError('Invalid state, need account details to call private API.')

        self.polling = True
        self._polling_thread = Thread(target=self._pollForever)
        self._polling_thread.setDaemon(True)
        self._polling_thread.start()

    # ----------
    # Low level HTTP request
    # ----------
    def _public(self, endpoint):
        """Send GET request to bitstamp. Return python dict."""

        url = self.url + endpoint

        _LOG.debug('Sending GET request: ' + url)
        res = req.get(url)

        if res.status_code // 100 != 2:
            _log_HTTP_error(res)
            raise ConnectionError

        res = json.loads(res.text)
        return res

    def _private(self, endpoint, **params):
        """Send POST request to bitstamp. Return python dict."""

        params.update(self._authParams())
        url = self.url + endpoint

        _LOG.debug('Sending POST request: ' + url)
        res = req.post(url, params)

        if res.status_code // 100 != 2:
            _log_HTTP_error(res)
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

    # ----------
    # Low level HTTP polling
    # ----------
    def _poll_forever(self):
        while True and self.polling:
            for order in self._open_orders:
                res = self._private('/order_status/', params={'id': order})
                if res['status'] == 'finished':
                    self._announce_orderfilled(order)
                    self._open_orders.remove(order)
            sleep(self.poll_rate)

    @event.source('orderfilled')
    def _announce_orderfilled(self, oid):
        return oid

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

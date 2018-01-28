from .utility  import *
from .strategy import Portfolio

import logging
import json
import csv


log = logging.getLogger('Exchange')


def backtest_tick(strat, dataset, pair=None, portfolio=None, exchange=None,
        commission=0.0012, slippage=0.0012, callback=None):
    '''Wrapper function for running backtest on tick based strategy.

    Args:
        pair: String representation of the trade coin pair (meta info)
        portfolio: Portfolio object to be assigned to the strategy
        exchange: Exchagne object to be assigned to the strategy and Backtest manager
        commission: Commission of this backtest. Ignored if an exchange was passed as argument
        slippage: Slippage of this backtest. Ignored if an exchange was passed as argument
        callback: Function to be called at the end of each tick

    Returns:
        The strategy object that was passed as argument

    Raise:
        Exceptions that may be raised by the strategy
    '''
    portfolio = portfolio or Portfolio(10000)
    exchange = exchange or PaperExchange(commission=commission, slippage=slippage)

    strat.pair = strat.pair or pair
    strat.portfolio = strat.portfolio or portfolio
    strat.exchange = strat.exchange or exchange

    test = Backtest(exchange)
    test.read(dataset)
    test.run(strat, callback)


# Only works with tick for now
class Backtest():
    '''Provides an interface to load datasets and launch backtests.'''

    def __init__(self, exchange=None):
        self.exchange = exchange or PaperExchange()

    def run(self, strat, callback=None):
        '''Run a tick strategy on the loaded dataset.

        Args:
            callback: A function taking (price, volume, timestamp, action) as parameter

        Raises:
            Does not raise exceptions.
        '''
        for tick in self.ticks:
            price, timestamp, volume, action= unpackTick(tick)
            self.exchange.price = price
            self.exchange.volume = volume
            self.exchange.timestamp = timestamp
            strat.pushTick(price, timestamp, volume, action)
            if callback:
                callback(strat)

    # Read file, detect it's data format and automatically parses it
    def read(self, fname, fileformat=None, fmt=None):
        raw = self._read(fname)
        fileformat = fileformat or self._guessFileType(raw[0])

        if fileformat == 'JSON':
            self.readJSON(fname)
        elif fileformat == 'CSV':
            self.readCSV(fname)
        elif fileformat == 'XML': # Not supported
            self.readString(fname)
        else:
            self.readString(fname)

    # Store ticks as list of strings
    def readString(self, fname):
        self.ticks = self._read(fname)

    # Not needed, Strategy now only supports json string
    def readJSON(self, fname):
        raw = self._read(fname)
        self.ticks = self._parseJSON(raw)

    # Not needed, Strategy now only supports json string
    def readCSV(self, fname, fieldnames=None):
        fieldnames = fieldnames or ['amount', 'price', 'timestamp']
        with open(fname) as f:
            reader = csv.DictReader(f, fieldnames=fieldnames)
            self.ticks = [row for row in reader]

    @staticmethod
    def _guessFileType(line):
        if line[0] == '{' or line[0] == '[':
            return 'JSON'
        elif line[0] == '<':
            return 'XML'
        elif ',' in line:
            return 'CSV'
        else:
            return None

    @staticmethod
    def _read(fname):
        with open(fname) as f:
            return f.read().splitlines()

    @staticmethod
    def _parseJSON(strings):
        return [json.loads(tick) for tick in strings]

    @staticmethod
    def _parseCSV(strings, fieldnames=None):
        x = []
        for s in strings:
            tx = {}
            s = s.split('n')
            for i, c in enumerate(s):
                tx[fieldnames[i]] = c


class PaperExchange:

    def __init__(self, commission=0, slippage=0):
        self.price = 0
        self.volume = 0
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
        return {'price': price, 'amount': amount, 'status': 'success', 'timestamp': self.timestamp}


    def marketSell(self, pair, amount):
        checkType(pair, str)
        checkType(amount, int, float)
        assert amount > 0

        price = self.price
        price *= (1 - self.commission)
        price *= (1 - self.slippage)

        log.info('Sell {:7.5g} {} @${:.5g}'.format(amount, pair.upper(), self.price))
        log.info('Paid {:.5g} commission'.format(self.price * self.commission))
        return {'price': price, 'amount': amount, 'status': 'success', 'timestamp': self.timestamp}


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
        return {'price': price, 'amount': amount, 'status': 'success', 'timestamp': self.timestamp}


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
        return {'price': price, 'amount': amount, 'status': 'success', 'timestamp': self.timestamp}


    def getCash(self, *args, **kws):
        raise NotImplementedError


    def getTicker(self, *args, **kws):
        raise NotImplementedError


    def getOrderbook(self, *args, **kws):
        raise NotImplementedError


    def getBalance(self, *args, **kws):
        raise NotImplementedError


    def getOrderStatus(self, *args, **kws):
        raise NotImplementedError


    def getOpenOrders(self, *args, **kws):
        raise NotImplementedError

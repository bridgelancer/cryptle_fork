from loglevel import *

import logging
import csv

log = logging.getLogger('Exchange')


class Backtest():

    def run(self, strat):
        for tick in self.ticks:
            strat(tick)

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


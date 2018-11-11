# @Incomplete data format is hardwired for bitstamp (or are we?)
# @Incomplete candle formatted data is not properly implemented

from .strategy import Portfolio, Strategy
from .event import source, Bus

import json
import csv
import logging
logger = logging.getLogger(__name__)


def backtest_with_bus(strat, dataset, dtype, *bindables, bus=None):
    """Convenience function for backtesting trade data with an event bus."""
    data_iterator = DataEmitter(dtype)

    if bus is None:
        bus = Bus()

    for bindable in bindables:
        bus.bind(bindable)

    bus.bind(strat)
    bus.bind(data_iterator)

    data_iterator.emitAll(dataset)


def backtest_tick(strat, dataset, bus=None, pair=None, portfolio=None, exchange=None,
        commission=0.0012, slippage=0, callback=None):
    """Wrapper function for running backtest on tick-based strategy.

    Args:
        dataset: Dataset to be read by the backtest. File format can be detected automatically
        pair: String representation of the trade coin pair (meta info)
        portfolio: Portfolio object to be assigned to the strategy
        exchange: Exchagne object to be assigned to the strategy and Backtest manager
        commission: Commission of this backtest. Ignored if an exchange was passed as argument
        slippage: Slippage of this backtest. Ignored if an exchange was passed as argument
        callback: Function to be called at the end of each tick

    Returns:
        Strategy object from input.

    Raise:
        Exceptions that may be raised by the strategy
    """
    portfolio = portfolio or Portfolio(10000)
    exchange = exchange or PaperExchange(commission=commission, slippage=slippage)

    strat.pair = strat.pair or pair
    strat.portfolio = strat.portfolio or portfolio
    strat.exchange = strat.exchange or exchange

    test = Backtest(exchange)
    if isinstance(bus, Bus):
        bus.bind(test)

    test.read(dataset)
    test.run(strat, callback)


def backtest_bar(strat, dataset, pair=None, portfolio=None, exchange=None,
        commission=0.0012, slippage=0, callback=None):
    """Wrapper function for running backtest on bar based strategy.

    Args:
        dataset: Dataset to be read by the backtest. File format can be detected automatically
        pair: String representation of the trade coin pair (meta info)
        portfolio: Portfolio object to be assigned to the strategy
        exchange: Exchagne object to be assigned to the strategy and Backtest manager
        commission: Commission of this backtest. Ignored if an exchange was passed as argument
        slippage: Slippage of this backtest. Ignored if an exchange was passed as argument
        callback: Function to be called at the end of each bar

    Returns:
        Strategy object from input.

    Raise:
        Exceptions that may be raised by the strategy
    """
    portfolio = portfolio or Portfolio(10000)
    exchange = exchange or PaperExchange(commission=commission, slippage=slippage)

    strat.pair = strat.pair or pair
    strat.portfolio = strat.portfolio or portfolio
    strat.exchange = strat.exchange or exchange

    test = Backtest(exchange)
    test.read(dataset)
    test.runCandle(strat, callback)


class DataEmitter:
    """Emitter that iterate over provided datasets and broadcast row by row.

    Attributes
    ----------
    dtype : str
        The expected financial data type of. Must be set before :meth:`emitAll()` is called.
    """
    def __init__(self, dtype):
        self.dtype = dtype

    def emitAll(self, dataset):
        if not self.dtype:
            raise ValueError('Expect emitter data type to be set')

        if self.dtype == 'candle':
            for data in dataset:
                self.emitCandle(data)
        elif self.dtype == 'trade':
            for data in dataset:
                self.emitTrade(data)
        else:
            raise TypeError('Unrecognized data type')

    @source('candles')
    def emitCandle(self, data):
        return data

    @source('trades')
    def emitTick(self, data):
        return data


class Backtest:
    """Provides an interface to load datasets and launch backtests."""

    def __init__(self, exchange=None):
        self.exchange = exchange or PaperExchange()
        self.ticks = None

    @source('tick')
    def emitTick(self, tick):
        return tick

    @source('candle')
    def emitCandle(self, candle):
        return candle

    def run(self, strat, callback=None):
        """Run a tick strategy on the loaded dataset.

        Args:
            callback: A function taking (price, volume, timestamp, action) as parameter
        """
        for tick in self.ticks:
            if not tick:
                raise ValueError('Expected dataset to be loaded, none found.')
            price, timestamp, volume, action= _unpack(tick)
            self.exchange.price = price
            self.exchange.volume = volume
            self.exchange.timestamp = timestamp
            if strat.__class__.__bases__[-1].__name__ == 'Strategy':
                strat.pushTick(price, timestamp, volume, action) # push the tick to strat
            # remember to change the name of strategy
            elif strat.__class__.__bases__[-1].__name__ == 'SingleAssetStrategy':
                # emit a tick Event to kickstart the SingleAssetStrat strategy
                # WARNING: check tick format to see whether it still fits dataset
                self.emitTick([float(price), float(volume), float(timestamp), float(action)])

            if callback:
                callback(strat)

    def runCandle(self, strat, callback=None):
        for candle in self.candles:
            o, c, h, l, t, v = candle
            self.exchange.price = c
            self.exchange.volume = v
            self.exchange.timestamp = t
            if strat.__name__ == 'Strategy':
                strat.pushCandle(o, c, h, l, t, v) # push the candle stick to strat
            elif strat.__name__ == 'NewStrategy':
                # emit a 'candle' Event to kickstart the new strategy
                pass
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


    # @Rename
    # Give the attritubes a better name
    # Use different names for different types of data

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
    """Stub for exchange objects. Only supports market/limit orders.

    When used with the OO backtest interface, it should be passed to the
    Backtest object such that the market price is updated while the strategy
    processeses incoming market information.
    """

    def __init__(self, commission=0, slippage=0):
        self.price = 0
        self.volume = 0
        self.timestamp = 0
        self.commission = commission
        self.slippage = slippage

    def sendMarketBuy(self, pair, amount):
        _price = self.price
        price *= (1 + self.commission)
        price *= (1 + self.slippage)

        logger.info('Buy  {:7.5g} {} @${:.5g}'.format(amount, pair.upper(), price))
        logger.info('Paid {:.5g} commission'.format(_price * self.commission))
        return {'price': price, 'amount': amount, 'status': 'success', 'timestamp': self.timestamp}

    def sendMarketSell(self, pair, amount):
        _price = self.price
        price *= (1 - self.commission)
        price *= (1 - self.slippage)

        logger.info('Sell {:7.5g} {} @${:.5g}'.format(amount, pair.upper(), self.price))
        logger.info('Paid {:.5g} commission'.format(_price * self.commission))
        return {'price': price, 'amount': amount, 'status': 'success', 'timestamp': self.timestamp}

    def sendLimitBuy(self, pair, amount, price):
        _price = price
        price *= (1 + self.commission)
        price *= (1 + self.slippage)

        logger.info('Buy  {:7.5g} {} @${:.5g}'.format(amount, pair.upper(), price))
        logger.info('Paid {:.5g} commission'.format(_price * self.commission))
        return {'price': price, 'amount': amount, 'status': 'success', 'timestamp': self.timestamp}

    def sendLimitSell(self, pair, amount, price):
        _price = price
        price *= (1 - self.commission)
        price *= (1 - self.slippage)

        logger.info('Sell {:7.5g} {} @${:.5g}'.format(amount, pair.upper(), price))
        logger.info('Paid {:.5g} commission'.format(_price * self.commission))
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


def _unpack(tick):
    price = tick['price']
    volume = tick['amount']
    timestamp = float(tick['timestamp'])
    if 'type' in tick:
        action = 1 - tick['type'] * 2
    else:
        action = 0
    return price, timestamp, volume, action

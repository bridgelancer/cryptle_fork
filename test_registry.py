from functools import wraps
import logging
import math
import time
import sys
import traceback
import log
import datetime

import pytest
import pandas as pd

from cryptle.backtest import *
from cryptle.exchange import Bitstamp
from cryptle.strategy import *
from cryptle.event import source, on, Bus
from cryptle.registry import Registry
from cryptle.loglevel import *
from cryptle.aggregator import Aggregator
from metric.timeseries.candle import CandleStick
from metric.timeseries.sma import SMA


logging.basicConfig(level=logging.DEBUG)
#dataset = pd.read_csv(open('bitstamp.csv'))
dataset = pd.read_csv(open('bitstamp.csv'))
tickset = pd.read_json(open('bch1.log'), convert_dates=False, lines=True)


def test_registry_construction():
    setup = {"testrun": [['open'], ['once per bar']], "testrun2": [['close'],['once per trade']]} # key value pairs that signify the constraints of each type of action
    registry = Registry(setup)
    assert registry.__dict__['setup'] == setup

# only activate when it is bar close
def test_on_close():
    setup = {'close': [['close'], [['once per bar'], {}]]}
    registry = Registry(setup)

    @source('aggregator:new_close')
    def parseClose(val):
        return val

    bus = Bus()
    bus.bind(parseClose)
    bus.bind(registry)
    for value in dataset['close']:
        parseClose(value)
    assert registry.close_price == 6453.99

## only activate when it is bar open
def test_on_open():
    setup = {'close': [['open'], [['once per bar'],{}]]}
    registry = Registry(setup)

    @source('aggregator:new_open')
    def parseOpen(val):
        return val

    bus = Bus()
    bus.bind(parseOpen)
    bus.bind(registry)
    for value in dataset['open']:
        parseOpen(value)
    assert registry.open_price == 6375.11

def test_on_tick():
    setup = {'close': [['open'], [['once per bar'], {}]]}
    registry = Registry(setup)
    @source('tick')
    def emitTick(tick):
        return tick
    bus = Bus()
    bus.bind(emitTick)
    bus.bind(registry)
    for index, tick in tickset.iterrows():
        data = [tick['price'], tick['amount'], tick['timestamp'], tick['type']]
        emitTick(data)
    assert registry.current_price == 995.0

# this works, only because of not listening to 'aggregator:new_candle'
def test_aggregator():
    aggregator = Aggregator(3600)
    @source('tick')
    def emitTick(tick):
        return tick

    bus = Bus()
    bus.bind(emitTick)
    bus.bind(aggregator)
    for index, tick in tickset.iterrows():
        data = [tick['price'], tick['amount'], tick['timestamp'], tick['type']]
        emitTick(data)
    #print(aggregator._bars[-1])


def test_handleTrigger():
    setup = {'twokprice': [['open'], [['once per bar', 'once per trade'], {}]]}
    registry = Registry(setup)

    @source('strategy:triggered')
    def emitTrigger():
        return 'twokprice'

    bus = Bus()
    bus.bind(emitTrigger)
    bus.bind(registry)

    emitTrigger()
    assert registry.logic_status == {'twokprice': {'bar': [1, 1, 0], 'trade': [1, 1, 0]}}

# this also implicitly tested once per bar function, verify by using -s flag to observe the print
# behaviour
def test_execute_after_trigger():
    setup = {'twokprice': [[], [['once per bar'], {}]]}
    registry = Registry(setup)
    aggregator = Aggregator(3600)

    # emit tick to trigger check
    @source('tick')
    def emitTick(tick):
        return tick

    # emit Trigger to enforce post-triggered restraints
    @source('strategy:triggered')
    def emitTrigger():
        return 'twokprice'

    # client code that mimics that actual logic tests implemented in Strategy instance
    @on('registry:execute')
    def twokprice(data):
        emitTrigger() # should pass its name (action name) to emitTrigger

    # intitiate and binding class instances and functions to Bus
    bus = Bus()
    bus.bind(emitTrigger)
    bus.bind(twokprice)
    bus.bind(registry)
    bus.bind(aggregator)
    bus.bind(emitTick)

    # Tick-generating for loop using default dataset
    for index, tick in tickset.iterrows():
        data = [tick['price'], tick['amount'], tick['timestamp'], tick['type']]
        emitTick(data)

def test_n_per_bar():
    setup = {'twokprice': [[], [[], {'n per bar': [3]}]]}
    registry = Registry(setup)
    aggregator = Aggregator(3600)

    # emit tick to trigger check
    @source('tick')
    def emitTick(tick):
        return tick

    # emit Trigger to enforce post-triggered restraints
    @source('strategy:triggered')
    def emitTrigger():
        return 'twokprice'

    # client code that mimics that actual logic tests implemented in Strategy instance
    @on('registry:execute')
    def twokprice(data):
        emitTrigger() # should pass its name (action name) to emitTrigger

    # intitiate and binding class instances and functions to Bus
    bus = Bus()
    bus.bind(emitTrigger)
    bus.bind(twokprice)
    bus.bind(registry)
    bus.bind(aggregator)
    bus.bind(emitTick)

    # Tick-generating for loop using default dataset
    for index, tick in tickset.iterrows():
        data = [tick['price'], tick['amount'], tick['timestamp'], tick['type']]
        emitTick(data)

def test_one_per_period():
    setup = {'twokprice': [[], [[], {'once per period': [3]}]]}
    registry = Registry(setup)
    aggregator = Aggregator(3600)

    # emit tick to trigger check
    @source('tick')
    def emitTick(tick):
        return tick

    # emit Trigger to enforce post-triggered restraints
    @source('strategy:triggered')
    def emitTrigger():
        return 'twokprice'

    # client code that mimics that actual logic tests implemented in Strategy instance
    @on('registry:execute')
    def twokprice(data):
        #print(data[1], data[2])
        emitTrigger() # should pass its name (action name) to emitTrigger

    # intitiate and binding class instances and functions to Bus
    bus = Bus()
    bus.bind(emitTrigger)
    bus.bind(twokprice)
    bus.bind(registry)
    bus.bind(aggregator)
    bus.bind(emitTick)

    # Tick-generating for loop using default dataset
    for index, tick in tickset.iterrows():
        data = [tick['price'], tick['amount'], tick['timestamp'], tick['type']]
        emitTick(data)

def test_n_per_period():
    setup = {'twokprice': [[], [[], {'n per period': [3, 3]}]]}
    registry = Registry(setup)
    aggregator = Aggregator(3600)

    # emit tick to trigger check
    @source('tick')
    def emitTick(tick):
        return tick

    # emit Trigger to enforce post-triggered restraints
    @source('strategy:triggered')
    def emitTrigger():
        return 'twokprice'

    # client code that mimics that actual logic tests implemented in Strategy instance
    @on('registry:execute')
    def twokprice(data):
        #print(data[1], data[2])
        emitTrigger() # should pass its name (action name) to emitTrigger

    # intitiate and binding class instances and functions to Bus
    bus = Bus()
    bus.bind(emitTrigger)
    bus.bind(twokprice)
    bus.bind(registry)
    bus.bind(aggregator)
    bus.bind(emitTick)

    # Tick-generating for loop using default dataset
    for index, tick in tickset.iterrows():
        data = [tick['price'], tick['amount'], tick['timestamp'], tick['type']]
        emitTick(data)

def test_once_per_bar_n_per_period():
    setup = {'twokprice': [[], [['once per bar'], {'n per period': [3, 5]}]]}
    registry = Registry(setup)
    aggregator = Aggregator(3600)

    # emit tick to trigger check
    @source('tick')
    def emitTick(tick):
        return tick

    # emit Trigger to enforce post-triggered restraints
    @source('strategy:triggered')
    def emitTrigger():
        return 'twokprice'

    # client code that mimics that actual logic tests implemented in Strategy instance
    @on('registry:execute')
    def twokprice(data):
        print(data[1], data[2])
        emitTrigger() # should pass its name (action name) to emitTrigger

    # intitiate and binding class instances and functions to Bus
    bus = Bus()
    bus.bind(emitTrigger)
    bus.bind(twokprice)
    bus.bind(registry)
    bus.bind(aggregator)
    bus.bind(emitTick)

    # Tick-generating for loop using default dataset
    for index, tick in tickset.iterrows():
        data = [tick['price'], tick['amount'], tick['timestamp'], tick['type']]
        emitTick(data)

def test_one_per_signal():
    setup      = {'twokprice': [['open'], [['once per bar'], {'once per signal': ['sma']}]]}#, 'sma':[[], [['once per bar'], {}]]}
    bus        = Bus()
    registry   = Registry(setup)
    bus.bind(registry)
    aggregator = Aggregator(3600, bus=bus)
    stick      = CandleStick(1, bus=bus)
    sma        = SMA(stick.o, 5)

    # emit tick to trigger check
    @source('tick')
    def emitTick(tick):
        return tick

    # emit Trigger to enforce post-triggered restraints
    @source('strategy:triggered')
    def emitPrintTrigger():
        return 'twokprice'

    # This exists purely because one function could not emit two types of events
    @source('signal')
    def emitSMATrigger(test, boolean):
        return [test, boolean]

    # sourcing 'strategy:triggered', only triggered if sma > last open
    @on('aggregator:new_candle')
    def aboveSMA(data):
        print(datetime.datetime.fromtimestamp(int(data[4])).strftime('%Y-%m-%d %H:%M:%S'),
                "SMA:", sma.value, "Open:", data[0])
        if sma.value < float(stick.o):
            emitSMATrigger('sma', True)
            return 'sma'
        else:
            emitSMATrigger('sma', False)
            return 'sma'


    # client code that mimics that actual logic tests implemented in Strategy instance
    @on('registry:execute')
    def twokprice(data):
        try:
            print("TRIGGERED", datetime.datetime.fromtimestamp(int(data[1])).strftime('%Y-%m-%d %H:%M:%S'), data[2], "\n")
        except:
            pass
        emitPrintTrigger() # should pass its name (action name) to emitTrigger

    # intitiate and binding class instances and functions to Bus
    bus.bind(emitTick)
    bus.bind(emitPrintTrigger)
    bus.bind(emitSMATrigger)
    bus.bind(aboveSMA)
    bus.bind(twokprice)

    # Tick-generating for loop using default dataset
    for index, tick in tickset.iterrows():
        data = [tick['price'], tick['amount'], tick['timestamp'], tick['type']]
        emitTick(data)

def test_n_per_signal():
    pass


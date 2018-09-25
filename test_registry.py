from functools import wraps
import logging
import math
import time
import sys
import traceback
import log

import pytest
import pandas as pd

from cryptle.backtest import *
from cryptle.exchange import Bitstamp
from cryptle.strategy import *
from cryptle.event import source, on, Bus
from cryptle.registry import Registry
from cryptle.loglevel import *
from cryptle.aggregator import Aggregator


logging.basicConfig(level=logging.DEBUG)
#dataset = pd.read_csv(open('bitstamp.csv'))
dataset = pd.DataFrame()
tickset = pd.read_json(open('data/bch.json'), convert_dates=False, lines=True)


#def test_registry_construction():
#    setup = {"testrun": [['open'], ['once per bar']], "testrun2": [['close'],['once per trade']]} # key value pairs that signify the constraints of each type of action
#    registry = Registry(setup)
#    assert registry.__dict__['setup'] == setup
#
## only activate when it is bar close
#def test_on_close():
#    setup = {'close': [['open'], ['once per bar']]}
#    registry = Registry(setup)
#
#    @source('close')
#    def parseClose(val):
#        return val
#
#    bus = Bus()
#    bus.bind(parseClose)
#    bus.bind(registry)
#    for value in dataset['close']:
#        parseClose(value)
#    assert registry.close_price == 6453.99
#
## only activate when it is bar open
#def test_on_open():
#    setup = {'close': [['open'], ['once per bar']]}
#    registry = Registry(setup)
#
#    @source('open')
#    def parseOpen(val):
#        return val
#
#    bus = Bus()
#    bus.bind(parseOpen)
#    bus.bind(registry)
#    for value in dataset['open']:
#        parseOpen(value)
#    assert registry.open_price == 6375.11
#
#def test_on_tick():
#    setup = {'close': [['open'], ['once per bar']]}
#    registry = Registry(setup)
#    @source('tick')
#    def emitTick(tick):
#        return tick
#
#    bus = Bus()
#    bus.bind(emitTick)
#    bus.bind(registry)
#    for index, tick in tickset.iterrows():
#        data = [tick['price'], tick['amount'], tick['timestamp'], tick['type']]
#        emitTick(data)
#    assert registry.current_price == 995.0
#
## this works, only because of not listening to 'aggregator:new_candle'
#def test_aggregator():
#    aggregator = Aggregator(3600)
#    @source('tick')
#    def emitTick(tick):
#        return tick
#
#    bus = Bus()
#    bus.bind(emitTick)
#    bus.bind(aggregator)
#    for index, tick in tickset.iterrows():
#        data = [tick['price'], tick['amount'], tick['timestamp'], tick['type']]
#        emitTick(data)
#
#    assert(aggregator._bars[-1] == [float(1013.94), float(995.0), float(1014.94), float(995.0),
#        float(1518066000.0), float(0.11807207), float(0.0)])
#

# only activate once per bar
def test_once_per_bar():
    setup = {'twokprice': [['open'], ['once per bar']]}
    registry = Registry(setup)
    aggregator = Aggregator(3600)

    @source('tick')
    def emitTick(tick):
        return tick

    #@on('tick')
    #def testOn(data):
    #    print(data)
    @source('strategy:triggered')
    def triggered():
        print('Fuck me')
        return 'triggered'

    @on('registry:execute')
    def twokprice(data):
        print('Fuck you')
        if data == "twokprice":
            if current_price > 2000:
                triggered()

    bus = Bus()
    bus.bind(emitTick)
    bus.bind(registry)
    bus.bind(aggregator)
    bus.bind(twokprice)
    #bus.bind(testOn)
    bus.bind(triggered)

    current_price = None

    for index, tick in tickset.iterrows():
        data = [tick['price'], tick['amount'], tick['timestamp'], tick['type']]
        emitTick(data)
        current_price = tick['price']

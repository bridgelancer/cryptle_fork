from cryptle.event import Bus, on, source
from cryptle.codeblock import CodeBlock
from cryptle.aggregator import Aggregator
from cryptle.newregistry import Registry

from metric.timeseries.candle import CandleStick
from metric.timeseries.rsi    import RSI

import transitions
import pytest
import pandas as pd
from datetime import datetime
from collections import ChainMap

try:
    dataset = pd.read_csv(open('bitstamp.csv'))
    tickset = pd.read_json(open('bch1.log'), convert_dates=False, lines=True)
except FileNotFoundError:
    dataset = pd.DataFrame()
    tickset = pd.DataFrame()

def test_construction():
    def CB1():
        #print('successful construction')
        return True, {}

    setup = ['open', [['once per bar'], {}], 1]
    cb1 = CodeBlock(CB1, setup)
    assert cb1.name == 'CB1'
    assert cb1.states == ['initialized', 'rest', 'checked', 'executed', 'triggered']

def test_on_close():
    def twokprice():
        flags = {"twokflag": True, 'twokflagfuckyou': True}
        if registry.current_price is not None:
            if registry.current_price > 1000:
                flags['twokflag'] = True
            else:
                flags['twokflag'] = False

        return True, flags

    setup = {twokprice: ['close', [['once per bar'], {}], 1]}
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

    def twokprice():
        flags = {"twokflag": True, 'twokflagfuckyou': True}
        if registry.current_price is not None:
            if registry.current_price > 1000:
                flags['twokflag'] = True
            else:
                flags['twokflag'] = False

        return True, flags

    setup = {twokprice: [['open'], [['once per bar'],{}], 1]}
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

def test_transition():
    def CB1():
        #print('successful transition')
        return True, {}, {}

    setup = ['open', [['once per bar'], {}], 1]
    cb1 = CodeBlock(CB1, setup)
    assert cb1.state == 'initialized'
    cb1.initializing()
    assert cb1.state == 'rest'
    cb1.checking(2, [])
    assert cb1.state == 'rest'


def test_registration_to_reigstry():
    def CB1():
        #print('successful regisration and execution CB1')
        pass

    def CB2():
        #print('successful registration and execution CB2')
        pass

    def CB3():
        #print('successful registration and execution CB3')
        pass

    setup = {CB1: ['open', [['once per bar'], {}], 1],
             CB2: ['close', [['once per bar'], {}], 2],
             CB3: ['open', [['once per bar'], {}], 3],
             }
    registry = Registry(setup)
    for item in registry.codeblocks:
        assert item.name == 'CB' + str(registry.codeblocks.index(item) + 1)
        #item.checking()

def test_initialization():
    def CB1():
        #print('successful regisration and execution CB1')
        pass

    def CB2():
        #print('successful registration and execution CB2')
        pass

    def CB3():
        #print('successful registration and execution CB3')
        pass

    def CB4():
        #print('successful registration and execution CB4')
        pass

    def CB5():
        #print('successful registration and execution CB5')
        pass

    def CB6():
        #print('successful registration and execution CB6')
        pass

    def CB7():
        #print('successful registration and execution CB7')
        pass

    def CB8():
        #print('successful registration and execution CB8')
        pass

    setup = {CB1: ['open', [['once per bar'], {}], 1],
             CB2: ['close', [['once per trade'], {}], 2],
             CB3: ['close', [[], {'once per period': [2]}], 3],
             CB4: ['open', [[], {'once per flag': [CB3, 'damn']}], 4], # this formats is wrong
             CB5: ['open', [[], {'n per bar': [3]}], 5],
             CB6: ['open', [[], {'n per period':[3, 2]}], 6],
             CB7: ['open', [[], {'n per trade':[3, 1]}], 7],
             CB8: ['open', [[], {'n per flag': [[CB6, 'damnson', 10000], ]}], 8],
             }

    registry = Registry(setup)
    assert registry.codeblocks[0].logic_status.logic_status == {'bar': [1, 1, 0]}
    assert registry.codeblocks[1].logic_status.logic_status == {'trade': [1, 1, 0]}
    assert registry.codeblocks[2].logic_status.logic_status == {'period': [1, 2, 0]}
    assert registry.codeblocks[3].logic_status.logic_status == {'damn': [1, 1, 0]}
    assert registry.codeblocks[4].logic_status.logic_status == {'bar': [3, 1, 0]}
    assert registry.codeblocks[5].logic_status.logic_status == {'period': [3, 2, 0]}
    assert registry.codeblocks[6].logic_status.logic_status == {'trade': [3, 1, 0]}
    assert registry.codeblocks[7].logic_status.logic_status == {'damnson': [10000, 1, 0]}

    for i in range(0, 8, 1):
        assert registry.codeblocks[i].state == 'rest'


#@pytest.mark.skip(reason='not implemented')
def test_is_executable():
    def CB1():
        #print('successful regisration and execution CB1')
        pass

    def CB2():
        #print('successful registration and execution CB2')
        pass

    def CB3():
        #print('successful registration and execution CB3')
        pass

    def CB4():
        #print('successful registration and execution CB4')
        pass

    def CB5():
        #print('successful registration and execution CB5')
        pass

    def CB6():
        #print('successful registration and execution CB6')
        pass

    def CB7():
        #print('successful registration and execution CB7')
        pass

    def CB8():
        #print('successful registration and execution CB8')
        pass

    setup = {CB1: ['open', [['once per bar'], {}], 1],
             CB2: ['close', [['once per trade'], {}], 2],
             CB3: ['close', [[], {'once per period': [2]}], 3],
             CB4: ['open', [[], {'once per flag': [CB3, 'damn']}], 4],
             CB5: ['open', [[], {'n per bar': [3]}], 5],
             CB6: ['open', [[], {'n per period':[3, 2]}], 6],
             CB7: ['open', [[], {'n per trade':[3, 1]}], 7],
             CB8: ['open', [[], {'n per flag': [[CB6, 'damnson', 10000], ]}], 8],
             }

    registry = Registry(setup)
    for i in range(0, 8, 1):
        assert registry.codeblocks[i].logic_status.is_executable() == True


def test_checking():
    def CB1():
        #print('successful enforce rudimentary checking CB1')
        return True, {}, {}

    def CB2():
        #print('successful enforce rudimentary checking CB2', registry.current_time)
        return True, {}, {}

    def CB3():
        #print('successful enforce rudimentary checking CB3')
        return True, {}, {}

    def CB4():
        #print('successful enforce rudimentary checking CB4', registry.current_time)
        return True, {}, {}

    setup = {
             CB1: ['open', [['once per bar'], {}], 1],
             CB2: ['open', [[], {'n per bar': [3]}], 2],
             CB3: ['open', [['once per bar'], {}], 3],
             CB4: ['open', [[], {'n per period': [4, 2]}], 4],
             }

    @source('tick')
    def emitTick(tick):
        return tick

    registry = Registry(setup)
    aggregator = Aggregator(3600)

    bus = Bus()
    bus.bind(emitTick)
    bus.bind(aggregator)
    bus.bind(registry)

    for index, tick in tickset.iterrows():
        data = [tick['price'], tick['amount'], tick['timestamp'], tick['type']]
        emitTick(data)

# Seems like it is working
def test_signals():
    def doneInit():
        flags = {"doneInitflag": True}
        return True, flags, {}

    def twokprice():
        flags = {"twokflag": True, 'twokflagfuckyou': True}
        if registry.current_price is not None:
            if registry.current_price > 980:
                flags['twokflag'] = True
            else:
                flags['twokflag'] = False

        return True, flags, {}

    # currently there is no mechnisitic ways to retrieve the last bar close time. Need a minor
    # workup in aggregator in data format to achieve it @REVIEW
    def CB2(*flagvaluedicts, testdata=None):
        flagValues = dict(ChainMap(*flagvaluedicts))
        print(flagValues)
        if registry.current_price < 990 and testdata:
            testdata = False
        else:
            testdata= True
        if flagValues['twokflag']:
            print('successfully check according to flag',
                    datetime.utcfromtimestamp(registry.current_time).strftime('%Y-%m-%d %H:%M:%S'), registry.close_price)

        flags = {}
        localdata = {'testdata': testdata}
        return True, flags, localdata

    setup = {
             doneInit: ['open', [['once per bar'], {}], 1],
             twokprice: ['open', [['once per bar'], {}], 2],
             CB2: ['open', [['once per bar'], {'n per flag': \
                 [[doneInit, 'doneInitflag', 100000], [twokprice, 'twokflag', 100], [twokprice,
                 'twokflagfuckyou', 10],]}], 3],
             }

    registry = Registry(setup)
    @source('tick')
    def emitTick(tick):
        return tick
    aggregator = Aggregator(3600)

    bus = Bus()
    bus.bind(emitTick)
    bus.bind(registry)
    bus.bind(aggregator)

    for index, tick in tickset.iterrows():
        data = [tick['price'], tick['amount'], tick['timestamp'], tick['type']]
        emitTick(data)

def test_localdata():
    rsi_period = 14
    rsi_upperthresh =70
    rsi_thresh = 40

    stick = CandleStick(180)
    rsi = RSI(stick.c, rsi_period)

    def doneInit():
        flags = {"doneInitflag": True}
        localdata = {}
        return True, flags, localdata

    def signifyRSI(doneInit, rsi_sell_flag=None, rsi_signal=None):
        try:
            if rsi > rsi_upperthresh:
                rsi_sell_flag = True
                rsi_signal = True
            elif rsi > 50:
                rsi_signal = True

            if rsi_sell_flag and rsi < 50:
                rsi_signal = False
            if rsi < rsi_thresh:
                rsi_sell_flag = False
                rsi_signal = False
            #print(rsi, datetime.utcfromtimestamp(registry.current_time).strftime('%Y-%m-%d %H:%M:%S'))
            #print(rsi_signal, rsi_sell_flag, "\n")
        except Exception as e:
            print(e)

        flags = {}
        localdata = {'rsi_sell_flag': rsi_sell_flag, 'rsi_signal': rsi_signal}
        return True, flags, localdata

    setup = {doneInit: ['', [['once per bar'], {}], 1],
            signifyRSI: ['open', [['once per bar'], {'n per flag':
        [[doneInit, 'doneInitflag', 1000000],]}], 1],
            }

    registry = Registry(setup)
    @source('tick')
    def emitTick(tick):
        return tick
    aggregator = Aggregator(180)

    bus = Bus()
    bus.bind(emitTick)
    bus.bind(registry)
    bus.bind(aggregator)
    bus.bind(stick)

    for index, tick in tickset.iterrows():
        data = [tick['price'], tick['amount'], tick['timestamp'], tick['type']]
        emitTick(data)

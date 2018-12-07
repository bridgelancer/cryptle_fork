from cryptle.event import Bus, on, source
from cryptle.codeblock import CodeBlock
from cryptle.aggregator import Aggregator
from cryptle.registry import Registry

from cryptle.metric.timeseries.candle import CandleStick
from cryptle.metric.timeseries.rsi    import RSI

from test.utils import get_sample_trades, get_sample_candles

import pytest
import pandas as pd
from datetime import datetime
from collections import ChainMap

dataset = get_sample_candles()
tickset = get_sample_trades()

#def test_construction():
#    def CB1():
#        #print('successful construction')
#        return True, {}
#
#    setup = ['open', [['once per bar'], {}], 1]
#    cb1 = CodeBlock(CB1, setup)
#    assert cb1.name == 'CB1'
#
#def test_on_close():
#    def twokprice():
#        flags = {"twokflag": True, 'twokflagyou': True}
#        if registry.current_price is not None:
#            if registry.current_price > 1000:
#                flags['twokflag'] = True
#            else:
#                flags['twokflag'] = False
#
#        return True, flags
#
#    setup = {twokprice: ['close', [['once per bar'], {}], 1]}
#    registry = Registry(setup)
#
#    @source('aggregator:new_close')
#    def parseClose(val):
#        return val
#
#    bus = Bus()
#    bus.bind(parseClose)
#    bus.bind(registry)
#
#    for value in dataset:
#        print(value[1])
#        parseClose(float(value[1]))
#    assert registry.close_price == 2727.97
#
### only activate when it is bar open
#def test_on_open():
#
#    def twokprice():
#        flags = {"twokflag": True, 'twokflagyou': True}
#        if registry.current_price is not None:
#            if registry.current_price > 1000:
#                flags['twokflag'] = True
#            else:
#                flags['twokflag'] = False
#
#        return True, flags
#
#    setup = {twokprice: [['open'], [['once per bar'],{}], 1]}
#    registry = Registry(setup)
#
#    @source('aggregator:new_open')
#    def parseOpen(val):
#        return val
#
#    bus = Bus()
#    bus.bind(parseOpen)
#    bus.bind(registry)
#    for value in dataset:
#        print(value[0])
#        parseOpen(float(value[0]))
#    assert registry.open_price == 2670.2
#
#
#def test_registration_to_reigstry():
#    def CB1():
#        #print('successful regisration and execution CB1')
#        pass
#
#    def CB2():
#        #print('successful registration and execution CB2')
#        pass
#
#    def CB3():
#        #print('successful registration and execution CB3')
#        pass
#
#    setup = {CB1: ['open', [['once per bar'], {}], 1],
#             CB2: ['close', [['once per bar'], {}], 2],
#             CB3: ['open', [['once per bar'], {}], 3],
#             }
#    registry = Registry(setup)
#    for item in registry.codeblocks:
#        assert item.name == 'CB' + str(registry.codeblocks.index(item) + 1)
#        #item.checking()
#
#def test_initialization():
#    def CB1():
#        #print('successful regisration and execution CB1')
#        pass
#
#    def CB2():
#        #print('successful registration and execution CB2')
#        pass
#
#    def CB3():
#        #print('successful registration and execution CB3')
#        pass
#
#    def CB4():
#        #print('successful registration and execution CB4')
#        pass
#
#    def CB5():
#        #print('successful registration and execution CB5')
#        pass
#
#    def CB6():
#        #print('successful registration and execution CB6')
#        pass
#
#    def CB7():
#        #print('successful registration and execution CB7')
#        pass
#
#    def CB8():
#        #print('successful registration and execution CB8')
#        pass
#
#    setup = {CB1: ['open', [['once per bar'], {}], 1],
#             CB2: ['close', [['once per trade'], {}], 2],
#             CB3: ['close', [[], {'once per period': [2]}], 3],
#             CB4: ['open', [[], {'once per flag': [CB3, 'damn']}], 4], # this formats is wrong
#             CB5: ['open', [[], {'n per bar': [3]}], 5],
#             CB6: ['open', [[], {'n per period':[3, 2]}], 6],
#             CB7: ['open', [[], {'n per trade':[3, 1]}], 7],
#             CB8: ['open', [[], {'n per flag': [[CB6, 'damnson', 10000], ]}], 8],
#             }
#
#    registry = Registry(setup)
#    assert registry.codeblocks[0].logic_status.logic_status == {'bar': [1, 1, 0]}
#    assert registry.codeblocks[1].logic_status.logic_status == {'trade': [1, 1, 0]}
#    assert registry.codeblocks[2].logic_status.logic_status == {'period': [1, 2, 0]}
#    assert registry.codeblocks[3].logic_status.logic_status == {'damn': [1, 1, 0]}
#    assert registry.codeblocks[4].logic_status.logic_status == {'bar': [3, 1, 0]}
#    assert registry.codeblocks[5].logic_status.logic_status == {'period': [3, 2, 0]}
#    assert registry.codeblocks[6].logic_status.logic_status == {'trade': [3, 1, 0]}
#    assert registry.codeblocks[7].logic_status.logic_status == {'damnson': [10000, 1, 0]}
#
##@pytest.mark.skip(reason='not implemented')
#def test_is_executable():
#    def CB1():
#        #print('successful regisration and execution CB1')
#        pass
#
#    def CB2():
#        #print('successful registration and execution CB2')
#        pass
#
#    def CB3():
#        #print('successful registration and execution CB3')
#        pass
#
#    def CB4():
#        #print('successful registration and execution CB4')
#        pass
#
#    def CB5():
#        #print('successful registration and execution CB5')
#        pass
#
#    def CB6():
#        #print('successful registration and execution CB6')
#        pass
#
#    def CB7():
#        #print('successful registration and execution CB7')
#        pass
#
#    def CB8():
#        #print('successful registration and execution CB8')
#        pass
#
#    setup = {CB1: ['open', [['once per bar'], {}], 1],
#             CB2: ['close', [['once per trade'], {}], 2],
#             CB3: ['close', [[], {'once per period': [2]}], 3],
#             CB4: ['open', [[], {'once per flag': [CB3, 'damn']}], 4],
#             CB5: ['open', [[], {'n per bar': [3]}], 5],
#             CB6: ['open', [[], {'n per period':[3, 2]}], 6],
#             CB7: ['open', [[], {'n per trade':[3, 1]}], 7],
#             CB8: ['open', [[], {'n per flag': [[CB6, 'damnson', 10000], ]}], 8],
#             }
#
#    registry = Registry(setup)
#    for i in range(0, 8, 1):
#        assert registry.codeblocks[i].logic_status.is_executable() == True
#
#
#def test_checking():
#    def CB1(flagValues, flagCB):
#        #print('successful enforce rudimentary checking CB1')
#        return True, {}, {}
#
#    def CB2(flagValues, flagCB):
#        #print('successful enforce rudimentary checking CB2', registry.current_time)
#        return True, {}, {}
#
#    def CB3(flagValues, flagCB):
#        #print('successful enforce rudimentary checking CB3')
#        return True, {}, {}
#
#    def CB4(flagValues, flagCB):
#        #print('successful enforce rudimentary checking CB4', registry.current_time)
#        return True, {}, {}
#
#    setup = {
#             CB1: ['open', [['once per bar'], {}], 1],
#             CB2: ['open', [[], {'n per bar': [3]}], 2],
#             CB3: ['open', [['once per bar'], {}], 3],
#             CB4: ['open', [[], {'n per period': [4, 2]}], 4],
#             }
#
#    @source('tick')
#    def emitTick(tick):
#        return tick
#
#    registry = Registry(setup)
#    aggregator = Aggregator(3600)
#
#    bus = Bus()
#    bus.bind(emitTick)
#    bus.bind(aggregator)
#    bus.bind(registry)
#
#    for tick in tickset:
#        data = [tick[0], tick[2], tick[1], tick[3]]
#        data = [float(x) for x in data]
#        emitTick(data)
#
## Seems like it is working
#def test_signals_and_augmented_dict_in_checking():
#    def doneInit(flagValues, flagCB):
#        flags = {"doneInitflag": True}
#        return True, flags, {}
#
#    def twokprice(flagValues, flagCB):
#        flags = {"twokflag": True, 'twokflagyou': True}
#        if registry.current_price is not None:
#            if registry.current_price > 980:
#                flags['twokflag'] = True
#            else:
#                flags['twokflag'] = False
#
#        return True, flags, {}
#
#    # currently there is no mechnisitic ways to retrieve the last bar close time. Need a minor
#    # workup in aggregator in data format to achieve it @REVIEW
#    def CB2(flagValues, flagCB, testdata=None):
#        if registry.current_price < 990 and testdata:
#            testdata = False
#        else:
#            testdata= True
#        if flagValues['twokflag']:
#            print('successfully check according to flag',
#                    datetime.utcfromtimestamp(registry.current_time).strftime('%Y-%m-%d %H:%M:%S'), registry.close_price)
#
#        flags = {}
#        localdata = {'testdata': testdata}
#        return True, flags, localdata
#
#    setup = {
#             doneInit: ['open', [['once per bar'], {}], 1],
#             twokprice: ['open', [['once per bar'], {}], 2],
#             CB2: ['open', [['once per bar'], {'n per flag': \
#                 [[doneInit, 'doneInitflag', 100000], [twokprice, 'twokflag', 100], [twokprice,
#                 'twokflagyou', 10],]}], 3],
#             }
#
#    registry = Registry(setup)
#    @source('tick')
#    def emitTick(tick):
#        return tick
#    aggregator = Aggregator(3600)
#
#    bus = Bus()
#    bus.bind(emitTick)
#    bus.bind(registry)
#    bus.bind(aggregator)
#
#    for tick in tickset:
#        data = [tick[0], tick[2], tick[1], tick[3]]
#        data = [float(x) for x in data]
#        emitTick(data)
#
#def test_localdata():
#    rsi_period = 14
#    rsi_upperthresh =70
#    rsi_thresh = 40
#
#    stick = CandleStick(180)
#    rsi = RSI(stick.c, rsi_period)
#
#    def doneInit(flagValues, flagCB):
#        flags = {"doneInitflag": True}
#        localdata = {}
#        return True, flags, localdata
#
#    def signifyRSI(flagValues, flagCB, rsi_sell_flag=None, rsi_signal=None):
#        try:
#            if rsi > rsi_upperthresh:
#                rsi_sell_flag = True
#                rsi_signal = True
#            elif rsi > 50:
#                rsi_signal = True
#
#            if rsi_sell_flag and rsi < 50:
#                rsi_signal = False
#            if rsi < rsi_thresh:
#                rsi_sell_flag = False
#                rsi_signal = False
#            #print(rsi, datetime.utcfromtimestamp(registry.current_time).strftime('%Y-%m-%d %H:%M:%S'))
#            #print(rsi_signal, rsi_sell_flag, "\n")
#        except Exception as e:
#            print(e)
#
#        flags = {}
#        localdata = {'rsi_sell_flag': rsi_sell_flag, 'rsi_signal': rsi_signal}
#        return True, flags, localdata
#
#    setup = {doneInit: ['', [['once per bar'], {}], 1],
#            signifyRSI: ['open', [['once per bar'], {'n per flag':
#        [[doneInit, 'doneInitflag', 1000000],]}], 1],
#            }
#
#    registry = Registry(setup)
#    @source('tick')
#    def emitTick(tick):
#        return tick
#    aggregator = Aggregator(180)
#
#    bus = Bus()
#    bus.bind(emitTick)
#    bus.bind(registry)
#    bus.bind(aggregator)
#    bus.bind(stick)
#
#    for tick in tickset:
#        data = [tick[0], tick[2], tick[1], tick[3]]
#        data = [float(x) for x in data]
#        emitTick(data)
#
#def test_set_local_data():
#    def doneInit(flagValues, flagCB):
#        flags = {"doneInitflag": True}
#        return True, flags, {}
#
#    def twokprice(flagValues, flagCB, twokflag=None, twokflagyou=True):
#        if registry.current_price is not None:
#            if registry.current_price > 980 and not twokflagyou:
#                twokflag = True
#            else:
#                twokflag = False
#                twokflagyou = True
#
#        flags = {"twokflag": twokflag, 'twokflagyou': twokflagyou}
#        localdata = {"twokflag": twokflag, "twokflagyou": twokflagyou}
#        return True, flags, localdata
#
#    def augmented(flagValues, flagCB, aug1=None, aug2=None, aug3=None):
#        aug1 = aug2 = aug3 = True
#        flags = {"aug1": aug1, "aug2": aug2, "aug3": aug3}
#        localdata = {"aug1": aug1, "aug2": aug2, "aug3": aug3}
#        return True, flags, localdata
#
#    # currently there is no mechnisitic ways to retrieve the last bar close time. Need a minor
#    # workup in aggregator in data format to achieve it @REVIEW
#    def CB2(flagValues, flagCB, testdata=None):
#        if registry.current_price > 990 and testdata:
#            testdata = False
#            flagCB['twokflagyou'].setLocalData({'twokflagyou': False})
#        else:
#            testdata= True
#            flagCB['twokflagyou'].setLocalData({'twokflagyou': True})
#
#        if flagValues['twokflag']:
#            print('successfully check according to flag',
#                    datetime.utcfromtimestamp(registry.current_time).strftime('%Y-%m-%d %H:%M:%S'), registry.close_price)
#
#        flags = {}
#        localdata = {'testdata': testdata}
#        return True, flags, localdata
#
#    setup = {
#             doneInit: ['open', [['once per bar'], {}], 1],
#             twokprice: ['open', [['once per bar'], {}], 2],
#             augmented: ['open', [['once per bar'], {}], 3],
#             CB2: ['open', [['once per bar'], {'n per flag': \
#                 [[doneInit, 'doneInitflag', 100000], [twokprice, 'twokflag', 100], [twokprice,
#                 'twokflagyou', 10], [augmented, 'aug1', 1],[augmented, 'aug2', 1],[augmented, 'aug3', 1],]}], 4],
#             }
#
#    registry = Registry(setup)
#    @source('tick')
#    def emitTick(tick):
#        return tick
#    aggregator = Aggregator(3600)
#
#    bus = Bus()
#    bus.bind(emitTick)
#    bus.bind(registry)
#    bus.bind(aggregator)
#
#    for tick in tickset:
#        data = [tick[0], tick[2], tick[1], tick[3]]
#        data = [float(x) for x in data]
#        emitTick(data)

def test_new_registry_format():
    def doneInit(flagValues, flagCB):
        flags = {"doneInitflag": True}
        return True, flags, {}

    def twokprice(flagValues, flagCB, twokflag=None, twokflagyou=True):
        if registry.current_price is not None:
            if registry.current_price > 980 and not twokflagyou:
                twokflag = True
            else:
                twokflag = False
                twokflagyou = True

        flags = {"twokflag": twokflag, 'twokflagyou': twokflagyou}
        localdata = {"twokflag": twokflag, "twokflagyou": twokflagyou}
        return True, flags, localdata

    def augmented(flagValues, flagCB, aug1=None, aug2=None, aug3=None):
        aug1 = aug2 = aug3 = True
        flags = {"aug1": aug1, "aug2": aug2, "aug3": aug3}
        localdata = {"aug1": aug1, "aug2": aug2, "aug3": aug3}
        return True, flags, localdata

    # currently there is no mechnisitic ways to retrieve the last bar close time. Need a minor
    # workup in aggregator in data format to achieve it @REVIEW
    def CB2(flagValues, flagCB, testdata=None):
        if registry.current_price > 990 and testdata:
            testdata = False
            flagCB['twokflagyou'].setLocalData({'twokflagyou': False})
        else:
            testdata= True
            flagCB['twokflagyou'].setLocalData({'twokflagyou': True})

        if flagValues['twokflag']:
            print('successfully check according to flag',
                    datetime.utcfromtimestamp(registry.current_time).strftime('%Y-%m-%d %H:%M:%S'), registry.close_price)

        flags = {}
        localdata = {'testdata': testdata}
        return True, flags, localdata

    setup = [
             (('codeblock', doneInit),
                        ('whenExec', 'open'),
                        ('once per bar', {'type': 'once per bar', 'event': 'bar',
                                         'refresh_period': 1})
                        ),
             (('codeblock', twokprice),
                         ('whenExec', 'open'),
                         ('once per bar', {'type': 'once per bar', 'event': 'bar',
                                         'max_trigger': 1, 'refresh_period': 1})
                         ),
             (('codeblock', augmented),
                         ('whenExec', 'open'),
                         ('once per bar', {'type': 'once per bar', 'event': 'bar',
                                         'max_trigger': 1, 'refresh_period': 1})
                         ),
             (('codeblock', CB2),
                         ('whenExec', 'open'),
                         ('once per bar', {'type': 'once per bar', 'event': 'bar',
                                         'max_trigger': 1, 'refresh_period': 1}),
                         ('doneInitflag', {'type': 'n per flag', 'event': 'flag',
                                         'max_trigger': 100000, 'refresh_period': 1,
                                         'funcpt': doneInit}),
                         ('twokflag',     {'type': 'n per flag', 'event': 'flag',
                                         'max_trigger': 100, 'refresh_period': 1,
                                         'funcpt': twokprice}),
                         ('twokflagyou',  {'type': 'n per flag', 'event': 'flag',
                                         'max_trigger': 100, 'refresh_period': 1,
                                         'funcpt': twokprice}),
                         ('aug1',         {'type': 'n per flag', 'event': 'flag',
                                         'max_trigger': 100, 'refresh_period': 1,
                                         'funcpt': augmented}),
                         ('aug2',         {'type': 'n per flag', 'event': 'flag',
                                         'max_trigger': 100, 'refresh_period': 1,
                                         'funcpt': augmented}),
                         ('aug3',         {'type': 'n per flag', 'event': 'flag',
                                         'max_trigger': 100, 'refresh_period': 1,
                                         'funcpt': augmented}),
                         ),
            ]


    registry = Registry(setup)

    @source('tick')
    def emitTick(tick):
        return tick

    aggregator = Aggregator(3600)

    bus = Bus()
    bus.bind(emitTick)
    bus.bind(registry)
    bus.bind(aggregator)

    for tick in tickset:
        data = [tick[0], tick[2], tick[1], tick[3]]
        data = [float(x) for x in data]
        emitTick(data)

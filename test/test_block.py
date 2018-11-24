from cryptle.codeblock import CodeBlock
from cryptle.newregistry import Registry
import transitions
import pandas as pd

try:
    dataset = pd.read_csv(open('bitstamp.csv'))
    tickset = pd.read_json(open('bch1.log'), convert_dates=False, lines=True)
except FileNotFoundError:
    dataset = pd.DataFrame()
    tickset = pd.DataFrame()

def test_construction():
    def CB1():
        print('successful construction')

    setup = ['open', [['once per bar'], {}], 1]
    cb1 = CodeBlock(CB1, setup)
    assert cb1.name == 'CB1'
    assert cb1.states == ['initialized', 'rest', 'checked', 'executed', 'triggered']


def test_transition():
    def CB1():
        print('successful construction')

    setup = ['open', [['once per bar'], {}], 1]
    cb1 = CodeBlock(CB1, setup)
    assert cb1.state == 'initialized'
    cb1.initialize()
    assert cb1.state == 'rest'
    cb1.checking()
    assert cb1.state == 'executed'
    cb1.passTrigger()
    assert cb1.state == 'triggered'
    cb1.cleanup()
    assert cb1.state == 'rest'


def test_registration_to_reigstry():
    def CB1():
        print('successful regisration and execution CB1')

    def CB2():
        print('successful registration and execution CB2')

    def CB3():
        print('successful registration and execution CB3')

    setup = {CB1: ['open', [['once per bar'], {}], 1],
             CB2: ['close', [['once per bar'], {}], 2],
             CB3: ['open', [['once per bar'], {}], 3],
             }
    registry = Registry(setup)
    for item in registry.codeblocks:
        assert item.name == 'CB' + str(registry.codeblocks.index(item) + 1)
        item.initialize()
        #item.checking()

def test_initialization():
    def CB1():
        print('successful regisration and execution CB1')

    def CB2():
        print('successful registration and execution CB2')

    def CB3():
        print('successful registration and execution CB3')

    def CB4():
        print('successful registration and execution CB4')

    def CB5():
        print('successful registration and execution CB5')

    def CB6():
        print('successful registration and execution CB6')

    def CB7():
        print('successful registration and execution CB7')

    def CB8():
        print('successful registration and execution CB8')

    setup = {CB1: ['open', [['once per bar'], {}], 1],
             CB2: ['close', [['once per trade'], {}], 2],
             CB3: ['close', [[], {'once per period': [2]}], 3],
             CB4: ['open', [[], {'once per signal': ['damn']}], 4],
             CB5: ['open', [[], {'n per bar': [3]}], 5],
             CB6: ['open', [[], {'n per period':[3, 2]}], 6],
             CB7: ['open', [[], {'n per trade':[3, 1]}], 7],
             CB8: ['open', [[], {'n per signal': [['damnson', 10000], ]}], 8],
             }

    registry = Registry(setup)
    for i in range(0, 8, 1):
        print(registry.codeblocks[i].logic_status.logic_status)

#def test_checking():
#    def CB1():
#        print('successful regisration and execution CB1')
#
#    def CB2():
#        print('successful registration and execution CB2')
#
#    def CB3():
#        print('successful registration and execution CB3')
#
#    setup = {CB1: ['open', [['once per bar'], {}], 1],
#             CB2: ['close', [['once per bar'], {}], 2],
#             CB3: ['open', [['once per bar'], {}], 3],
#             }
#
#    bus = Bus()
#    registry = Registry(setup, bus=bus)
#    @source('tick')
#    def emitTick(tick):
#        return tick
#
#    bus.bind(emitTick)
#
#    for index, tick in tickset.iterrows():
#        data = [tick['price'], tick['amount'], tick['timestamp'], tick['type']]
#        emitTick(data)


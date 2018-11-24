from cryptle.codeblock import CodeBlock
from cryptle.newregistry import Registry
import transitions


def test_construction():
    def CB1():
        print('successful construction')

    setup = ['open', [['once per bar'], {}], 1]
    cb1 = CodeBlock(CB1, setup)
    assert cb1.name == 'CB1'
    assert cb1.states == ['initialized', 'rest', 'checked', 'executed', 'triggered']
    print(cb1.machine)

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
        item.checking()


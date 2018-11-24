from cryptle.codeblock import CodeBlock
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

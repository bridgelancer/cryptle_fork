from cryptle.codeblock import CodeBlock
import transitions

def test_construction():
    def CB1():
        print('successful construction')

    setup = ['open', [['once per bar'], {}], 1]
    cb1 = CodeBlock(CB1, setup)
    assert cb1.name == 'CB1'
    assert cb1.states == ['initialized', 'rest', 'checked', 'executed', 'triggered']

def test_integreation_with_strat():
    pass

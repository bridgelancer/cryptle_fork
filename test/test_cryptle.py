import sys

import logging

from cryptle.strategy import Portfolio, Strategy, EventOrderMixin
import cryptle.logging


class DummyStrat(Strategy):
    def __init__(s, **kws):
        s.indicators = {}
        super().__init__(**kws)

    def generateSignal(s, price, ts, volume, action):
        pass

    def execute(s, ts):
        pass


def test_portfolio_constructor():
    port = Portfolio(cash=1000)
    assert port.cash == 1000

    port = Portfolio(cash=1000, balance={'usd': 3000})
    assert port.cash == 1000

    port = Portfolio(balance={'usd': 3000})
    assert port.cash == 3000


def test_equity():
    values = {'eth': 400}
    port  = Portfolio()

    port.deposit('eth', 10)
    assert port.equity(values) == 4000

    port.withdraw('eth', 5)
    assert port.equity(values) == 2000

    port.deposit('eth', 10)
    assert port.equity(values) == 6000

    port.withdraw('eth', 15)
    assert port.equity(values) == 0
    assert 'eth' not in port.balance


def test_strategy_base():
    strat = Strategy()
    assert strat.portfolio.cash == 0
    assert strat.exchange is None


def test_extended_strategy():
    class Strat(EventOrderMixin, Strategy):
        pass

    strat = Strat()
    assert strat.marketBuy.__func__ is EventOrderMixin.marketBuy

import sys
import logging

import pytest

import cryptle.logging
import test.utils as utils
from cryptle.backtest import DataEmitter, backtest_tick, backtest_with_bus
from cryptle.strategy import Portfolio, Strategy, EventOrderMixin


sample_trades = utils.get_sample_trades()
sample_candles = utils.get_sample_candles()


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


def test_strategy_mixin_mro():
    class Strat(EventOrderMixin, Strategy):
        pass

    strat = Strat()

    # unbound methods
    assert Strat.__init__ is Strategy.__init__

    # bound methods
    assert strat.__init__.__func__ is Strategy.__init__
    assert strat.marketBuy.__func__ is EventOrderMixin.marketBuy


def test_backtest_helpers():

    # strategy has no marked methods for binding, bus raise
    strat = Strategy()
    with pytest.raises(ValueError):
        backtest_with_bus(strat, sample_trades, 'trade')

    # base strategy raises from lack of callback implementations
    # create an instance of temporary type from oneline
    strat = type('QuickStrat', (EventOrderMixin, Strategy), {})()
    with pytest.raises(AttributeError):
        backtest_tick(strat, sample_trades)

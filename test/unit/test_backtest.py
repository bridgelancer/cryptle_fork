import sys
import logging

import pytest

import test.utils as utils
from cryptle.backtest import DataEmitter, backtest_tick, backtest_with_bus
from cryptle.strategy import Strategy, EventOrderMixin


@pytest.fixture
def trades(scope='module'):
    return utils.get_sample_trades()


@pytest.fixture
def candles(scope='module'):
    return utils.get_sample_candles()


def test_backtest_helpers(trades):

    # bus raises when an unbindable object is passed to bind() method
    # (strategy has no marked methods)
    strat = Strategy()
    with pytest.raises(ValueError):
        backtest_with_bus(strat, trades, 'trade')

    # base strategy raises from lack of callback implementations
    # create an instance of temporary type from oneline
    strat = type('QuickStrat', (EventOrderMixin, Strategy), {})()
    with pytest.raises(AttributeError):
        backtest_tick(strat, trades)

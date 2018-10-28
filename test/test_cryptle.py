import logging
import math
import time
import sys
import traceback
from functools import wraps

from cryptle.backtest import Backtest
from cryptle.exchange import Bitstamp
from cryptle.strategy import Portfolio, Strategy
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

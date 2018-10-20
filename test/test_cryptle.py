import logging
import math
import time
import sys
import traceback
from functools import wraps

from cryptle.backtest import Backtest
from cryptle.exchange import Bitstamp
from cryptle.strategy import Portfolio, Strategy
import cryptle.loglevel


class DummyStrat(Strategy):
    def __init__(s, **kws):
        s.indicators = {}
        super().__init__(**kws)

    def generateSignal(s, price, ts, volume, action):
        pass

    def execute(s, ts):
        pass


def test_equity():
    port  = Portfolio(10000)

    port.deposit('ethusd', 10, 1300)
    assert port.equity == 23000

    port.withdraw('ethusd', 5)
    assert port.equity == 16500

    port.deposit('ethusd', 5, 1000)
    assert port.equity == 21500

    port.withdraw('ethusd', 10)
    assert port.equity == 10000


def test_backtest_class():
    test = Backtest()


if __name__ == '__main__':
    formatter = logging.Formatter(fmt='%(name)s: [%(levelname)s] %(message)s')

    sh = logging.StreamHandler()
    sh.setLevel(logging.REPORT)
    sh.setFormatter(formatter)

    logger = logging.getLogger('Unittest')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(sh)

    fh = logging.FileHandler('unittest.log', mode='w')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)

    crylog = logging.getLogger('Cryptle')
    crylog.setLevel(logging.INFO)
    crylog.addHandler(fh)

    run_all_tests()

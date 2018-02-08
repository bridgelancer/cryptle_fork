from cryptle.backtest import *
from cryptle.exchange import Bitstamp
from cryptle.strategy import *
from cryptle.utility  import *

from functools import wraps
import logging
import math
import time
import sys
import traceback


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


# Unittest logging helpers
RESET   = '\033[0m'
COLOR   = '\033[%dm'
DIM     = '\033[%d;2m'
BOLD    = '\033[01;%dm'
RED     = BOLD % 31
YELLOW  = BOLD % 33
GREEN   = COLOR % 32
GREY    = COLOR % 90


def PASS(testname):
    logger.report(GREEN + 'Passed ' + GREY + testname + RESET)


def FAIL(testname):
    logger.report(YELLOW + 'Failed ' + RESET + testname)


def FATAL(testname):
    logger.report(RED + 'ERROR  ' + RESET + testname)


# Unittest testsuite setup
tests = []
def unittest(func):
    @wraps(func)
    def func_wrapper(*args, **kargs):
        try:
            func(*args, **kargs)
            PASS(func.__name__)
        except AssertionError:
            _, _, tb = sys.exc_info()
            tb_info = traceback.extract_tb(tb)
            _, line, _, text = tb_info[-1]
            FAIL('{}: Line {}: {}'.format(func.__name__, line, text))
        except Exception as e:
            FATAL('{}: {}: {}'.format(func.__name__, type(e).__name__, e))
    tests.append(func_wrapper)
    return func_wrapper


def run_all_tests():
    global tests
    for test in tests:
        test()


class DummyStrat(Strategy):
    def __init__(s, **kws):
        s.indicators = {}
        super().__init__(**kws)

    def generateSignal(s, price, ts, volume, action):
        pass

    def execute(s, ts):
        pass


@unittest
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


@unittest
def test_truncate():
    assert 0.123 == truncate(0.123198211212, 3)
    assert 0.1231982 == truncate(0.123198211212, 7)

    assert 0.231 != truncate(0.9121, 21)
    assert 0.3121 == truncate(0.3121, 12)


@unittest
def test_unpack():
    tick = {'price': 123, 'amount': 10, 'timestamp': 151221231, 'type': 0}
    price, timestamp, volume, action = unpackTick(tick)

    assert price == 123
    assert volume == 10
    assert timestamp == 151221231
    assert action == 1


@unittest
def test_backtest_class():
    test = Backtest()


@unittest
def test_backtest_tick():
    strat = DummyStrat()


@unittest
def test_exchange():
    bs = Bitstamp()
    bs.getTicker('bchusd')


if __name__ == '__main__':
    run_all_tests()

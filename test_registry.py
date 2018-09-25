from cryptle.backtest import *
from cryptle.exchange import Bitstamp
from cryptle.strategy import *
from cryptle.event import source, on, Bus
from cryptle.registry import Registry
from cryptle.loglevel import *

from functools import wraps
import logging
import math
import time
import sys
import traceback
import log
import pandas as pd


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


def run_all_tests(dataset):
    global tests
    for test in tests:
        test(dataset)


class DummyStrat(Strategy):
    def __init__(s, **kws):
        s.indicators = {}
        super().__init__(**kws)

    def generateSignal(s, price, ts, volume, action):
        pass

    def execute(s, ts):
        pass

@unittest
def test_registry_construction(dataset):
    setup = {"testrun": [['open'], ['once per bar']], "testrun2": [['close'],['once per trade']]} # key value pairs that signify the constraints of each type of action
    registry = Registry(setup)
    assert registry.__dict__['setup'] == setup

# only activate when it is bar close
@unittest
def test_on_close(dataset):
    setup = {'close': [['open'], ['once per bar']]}
    registry = Registry(setup)

    @source('close')
    def parseClose(val):
        return val

    bus = Bus()
    bus.bind(parseClose)
    bus.bind(registry)
    for value in dataset['close']:
        parseClose(value)

    print(registry.close_price)

# only activate when it is bar open
@unittest
def test_on_open(dataset):
    setup = {'close': [['open'], ['once per bar']]}
    registry = Registry(setup)


# only activate once per bar
@unittest
def test_once_per_bar(dataset):
    pass

# only exit at most n times per position
@unittest
def test_n_exits_per_trade(dataset):
    pass

# do not do anything before the screened position is closed
@unittest
def test_screened(dataset):
    pass

if __name__ == "__main__":
    dataset = pd.read_csv(open('bitstamp.csv'))
    run_all_tests(dataset)

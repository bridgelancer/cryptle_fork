from metric.candle import *
from metric.generic import *

from functools import wraps
import logging
import math
import time
import sys
import traceback


formatter = logging.Formatter(fmt='%(name)s: [%(levelname)s] %(message)s')

sh = logging.StreamHandler()
sh.setLevel(logging.INFO)
sh.setFormatter(formatter)

fh = logging.FileHandler('unittest.log', mode='w')
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)

logger = logging.getLogger('Unittest')
logger.setLevel(logging.DEBUG)
logger.addHandler(sh)
logger.addHandler(fh)


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
    logger.info(GREEN + 'Passed ' + GREY + testname + RESET)


def FAIL(testname):
    logger.info(YELLOW + 'Failed ' + RESET + testname)


def FATAL(testname):
    logger.info(RED + 'ERROR  ' + RESET + testname)


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


# Initialise sample series
const       = [3 for i in range(1, 100)]
lin         = [i for i in  range(1, 100)]
quad        = [i**2 for i in range(1, 100)]
alt_quad    = [(100+ ((-1) ** i) * (i/4)**2) for i in range (1, 100)]
logistic    = [(10 / (1 + 100 * math.exp(-i/10))) for i in range(1, 100)]
sine        = [(100 + (i/4) * (2* math.sin(i) ** 3 * i - math.sin(i) ** 5) / 2 / (i / 1.5)) for i in range(1, 100)]


@unittest
def test_sma():
    sma = simple_moving_average(const, 3)
    for val in sma:
        assert val == 3

    sma = simple_moving_average(lin, 3)
    for i, val in enumerate(sma):
        assert val == i + 2


@unittest
def test_wma():
    wma = weighted_moving_average(const, 5)
    for val in wma:
        assert val == 3

    wma = weighted_moving_average(lin, 4)
    for i, val in enumerate(wma):
        assert val - (i + 3) < 1e-6

    wma = weighted_moving_average(quad, 4)
    for i, val in enumerate(wma):
        assert val - (i**2 + 6*i + 10) < 1e-6


@unittest
def test_ema():
    ema = exponential_moving_average(const, 3)
    for val in ema:
        assert val == 3

    ema = exponential_moving_average(lin, 3)


if __name__ == '__main__':
    run_all_tests()

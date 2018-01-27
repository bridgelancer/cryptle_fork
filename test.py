from cryptle.backtest import *
from cryptle.strategy import *
from cryptle.utility  import *
from cryptle.loglevel import defaultFormatter
from ta import *

from functools import wraps
import logging
import math
import time
import sys
import traceback


formatter = defaultFormatter()

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
crylog.setLevel(logging.INDEX)
crylog.addHandler(fh)


# Unit Test helpers
RESET   = "\033[0m"
COLOR   = "\033[%dm"
RED     = COLOR % 31
GREEN   = COLOR % 32
YELLOW  = COLOR % 33


def PASS(testname):
    logger.report(GREEN + 'Passed ' + RESET + testname)


def FAIL(testname):
    logger.report(YELLOW + 'Failed ' + RESET + testname)


def FATAL(testname):
    logger.report(RED + 'ERROR  ' + RESET + testname)


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
            FATAL('{} raised {}: {}'.format(func.__name__, type(e).__name__, e))
    tests.append(func_wrapper)
    return func_wrapper

tests = []


@unittest
def testEquity():
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
def testTruncate():
    assert 0.123 == truncate(0.123198211212, 3)
    assert 0.1231982 == truncate(0.123198211212, 7)

    assert 0.231 != truncate(0.9121, 21)
    assert 0.3121 == truncate(0.3121, 12)


@unittest
def testTickUnpack():
    tick = {'price': 123, 'amount': 10, 'timestamp': 151221231, 'type': 0}
    price, timestamp, volume, action = unpackTick(tick)

    assert price == 123
    assert volume == 10
    assert timestamp == 151221231
    assert action == 1


# @Regression
@unittest
def testCVWMA():
    line = [(i, 1, i) for i in range(15)]
    quad = [(i, i+1, i) for i in range(15)]
    sine = [(math.sin(i), 1, i) for i in range(15)]

    thre_line = ContinuousVWMA(3)
    thre_quad = ContinuousVWMA(3)
    thre_sine = ContinuousVWMA(3)

    five_line = ContinuousVWMA(5)
    five_quad = ContinuousVWMA(5)
    five_sine = ContinuousVWMA(5)

    five_ma = []
    thre_ma = []
    for tick in line:
        thre_line.update(tick[0], tick[1], tick[2], 1)
        five_line.update(tick[0], tick[1], tick[2], 1)
        thre_ma.append(thre_line.dollar_volume)
        five_ma.append(five_line.dollar_volume)

    assert thre_ma[3] == 2
    assert five_ma[13] == 11
    thre_ma.clear()
    five_ma.clear()

    for tick in quad:
        thre_quad.update(tick[0], tick[1], tick[2], 1)
        five_quad.update(tick[0], tick[1], tick[2], 1)
        thre_ma.append(thre_quad.dollar_volume)
        five_ma.append(five_quad.dollar_volume)

    logger.debug(str(thre_ma[3]) + ' ' + str(thre_ma[8]) + ' ' + str(thre_ma[13]))
    logger.debug(str(five_ma[3]) + ' ' + str(five_ma[8]) + ' ' + str(five_ma[13]))
    thre_ma.clear()
    five_ma.clear()

    for tick in sine:
        five_sine.update(tick[0], tick[1], tick[2], 1)
        thre_sine.update(tick[0], tick[1], tick[2], 1)
        thre_ma.append(thre_sine.dollar_volume)
        five_ma.append(five_sine.dollar_volume)

    logger.debug(str(thre_ma[3]) + ' ' + str(thre_ma[8]) + ' ' + str(thre_ma[13]))
    logger.debug(str(five_ma[3]) + ' ' + str(five_ma[8]) + ' ' + str(five_ma[13]))


const = [(3, i) for i in range(1, 100)]
lin = [(i, i) for i in  range(1, 100)]
quad  = [(i**2, i) for i in range(1, 100)]
alt_quad = [((100+ ((-1) ** i) * (i/4)**2), i) for i in range (1, 33)]


@unittest
def testSMA():
    candle = CandleBar(1)
    sma = SMA(candle, 3)

    for tick in const:
        candle.update(tick[0], tick[1])
        if tick[1] < 5: continue
        else: assert sma.sma == 3

    for tick in lin:
        candle.update(tick[0], tick[1])
        if tick[1] < 5: continue
        else: assert sma.sma == tick[1] - 1


@unittest
def testEMA():
    candle = CandleBar(1)
    ema = EMA(candle, 3)

    for tick in const:
        candle.update(tick[0], tick[1])
        if tick[1] < 5: continue
        else: assert ema.ema == 3

    for tick in lin:
        candle.update(tick[0], tick[1])


@unittest
def testWMA():

    candle = CandleBar(1)   # 1 second bar
    wma = WMA(candle, 5)    # 5 bar look ac

    for tick in const:
        candle.update(tick[0], tick[1])
    assert wma.wma == 3.0

    for tick in lin:
        candle.update(tick[0], tick[1])
    assert wma.wma - (293 / 3) < 1e-5


@unittest
def testBollingerBand():

    candle = CandleBar(1)
    sma_5 = SMA(candle, 5)
    bb = BollingerBand(sma_5, 5)

    for tick in quad:
        candle.update(tick[0], tick[1])
    assert bb.width - 274.36253388 < 1e-5


@unittest
def testRSI():

    candle = CandleBar(1)
    candle_quad = CandleBar(1)
    candle_alt_quad = CandleBar(1)

    rsi_lin = RSI(candle, 14)
    rsi_quad = RSI(candle_quad, 14)
    rsi_alt_quad = RSI(candle_alt_quad, 14)

    for tick in lin:
        candle.update(tick[0], tick[1])
    assert rsi_lin.rsi == 100

    for tick in quad:
        candle_quad.update(tick[0], tick[1])
    assert rsi_quad.rsi == 100

    for tick in alt_quad:
        candle_alt_quad.update(tick[0], tick[1])
    assert rsi_alt_quad.rsi - 55.48924 < 1e-5


if __name__ == '__main__':
    for test in tests:
        test()

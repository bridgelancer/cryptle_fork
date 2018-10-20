from functools import wraps
import logging
import math
import time
import sys
import traceback

from cryptle.loglevel import *
from metric.base import *
from metric.candle import *
from metric.generic import *


# Initialise sample series
const       = [3 for i in range(1, 100)]
lin         = [i for i in  range(1, 100)]
quad        = [i**2 for i in range(1, 100)]
alt_quad    = [(100+ ((-1) ** i) * (i/4)**2) for i in range (1, 100)]
logistic    = [(10 / (1 + 100 * math.exp(-i/10))) for i in range(1, 100)]
sine        = [(100 + (i/4) * (2* math.sin(i) ** 3 * i - math.sin(i) ** 5) / 2 / (i / 1.5)) for i in range(1, 100)]

some_data = [
    -1.82348457,
    -0.13819782,
    1.25618544,
    -0.54487136,
    -2.24769311,
    9.82204284,
    -1.0181088,
    3.93764179,
    -8.73177678,
    5.99949843
]

def gaussian(mu, sig, start=0, end=100, interval=1):
    return [math.exp((x - mu) ** 2 / (2 * sig ** 2)) for x in range(start, end, interval)]


def test_generic_sma():
    sma = simple_moving_average(const, 3)
    for val in sma:
        assert val == 3

    sma = simple_moving_average(lin, 3)
    for i, val in enumerate(sma):
        assert val == i + 2


def test_generic_wma():
    wma = weighted_moving_average(const, 5)
    for val in wma:
        assert val == 3

    wma = weighted_moving_average(lin, 4)
    for i, val in enumerate(wma):
        assert val - (i + 3) < 1e-6

    wma = weighted_moving_average(quad, 4)
    for i, val in enumerate(wma):
        assert val - (i**2 + 6*i + 10) < 1e-6


def test_generic_ema():
    ema = exponential_moving_average(const, 3)
    for val in ema:
        assert val == 3

    ema = exponential_moving_average(lin, 3)
    for i, val in enumerate(ema):
        assert val/(i + 3) < 1


def test_generic_bollinger_width():
    result = bollinger_width(quad, 5)
    assert result[-1] - 274.36253388 < 1e-5


def test_generic_macd():
    diff, diff_ma  = macd(sine, 5, 8, 3)
    assert abs(diff[-1] + 3.08097455232022) < 1e-6
    assert abs(diff_ma[-1] - 0.5843467703997498) < 1e-6
    assert len(diff) == len(diff_ma)


def test_generic_pelt():
    gauss = gaussian(0, 1, start=-10, end=10, interval=1)
    random_shit = [1, -10, 100, -1000]
    constant = [1 for i in range(5)]
    linear = [i+1 for i in range(5)]
    #cps = pelt(gauss, cost_normal_var)
    #cps = pelt(random_shit, cost_normal_var)
    #cps = pelt(some_data, cost_normal_var)
    #cps = pelt(constant, cost_normal_var)
    #cps = pelt(linear, cost_normal_var)
    #cps = pelt(lin, cost_normal_var)
    #cps = pelt(quad, cost_normal_var)


def test_generic_difference():
    result = difference(quad)
    assert result[-1] - 197 < 1e-5


def test_metric_base():
    a = Metric()
    b = Metric()
    a.value = 1
    b.value = 2
    assert a + b == 3
    assert a - b == -1
    assert b + a == 3
    assert b - a == 1
    assert a / b == 0.5
    assert b // a == 2.0
    c = Metric()
    c.value = 5
    assert b / c == 0.4
    assert c % b == 1


def test_candle():
    c = Candle(4, 7, 10, 3, 12316, 1, 1)
    assert c.open == 4
    assert c.close == 7
    assert c.high == 10
    assert c.low == 3
    assert c.timestamp == 12316
    assert c.volume == 1
    assert c.netvol == 1
    c.open += 2
    c.close -= 4
    c.high += 3
    c.low -= 2
    c.volume += 3
    c.netvol -= 1
    assert c.open == 6
    assert c.close == 3
    assert c.high == 13
    assert c.low == 1
    assert c.volume == 4
    assert c.netvol == 0


def test_candelbar():
    bar = CandleBar(10)
    for i, tick in enumerate(const):
        bar.pushTick(tick, i)
        assert bar.last_close == const[0]
        assert bar.last_open == const[0]
        assert bar.last_high == const[0]
        assert bar.last_low == const[0]

    # Linear 1 tick per second
    bar = CandleBar(10)
    for i, tick in enumerate(lin):
        bar.pushTick(tick, i)
        assert bar.last_close == tick
        assert bar.last_high == tick

    assert isinstance(bar[-1].open, int)
    assert isinstance(bar[-1].close, int)
    assert isinstance(bar[-1].high, int)
    assert isinstance(bar[-1].low, int)
    assert isinstance(bar[-1].timestamp, int)
    assert bar[-1].volume == 0

    # 1 tick per 10 seconds
    bar = CandleBar(5)
    for i, tick in enumerate(lin):
        bar.pushTick(tick, i * 10)
        assert bar.last_close == tick
        assert bar.last_high == tick
        assert len(bar) == i * 2 + 1


def test_candle_sma():
    bar = CandleBar(4)
    ma = SMA(bar, 5)

    for i, price in enumerate(const):
        bar.pushTick(price, i)
        if i >= 20:
            assert ma == const[0]

    for i, price in enumerate(lin):
        bar.pushTick(price, i)
        if i >= 120:
            assert ma == i - 2


def test_candle_wma():
    bar = CandleBar(4)
    ma = WMA(bar, 5)

    for i, price in enumerate(const):
        bar.pushTick(price, i)
        if i >= 21:
            assert ma == 3.0

    for i, price in enumerate(lin):
        bar.pushTick(price, i)
        if i >= 120:
            assert ma - i + 1


def test_candle_ema():
    bar = CandleBar(4)
    ma = EMA(bar, 5)

    for i, price in enumerate(const):
        bar.pushTick(price, i)
        if i >= 20:
            assert ma - 3 < 1e-6

    for i, price in enumerate(lin):
        bar.pushTick(price, i)
        if i >= 120:
            assert ma - 3 < 1e-6


def test_candle_bollinger():
    bar = CandleBar(1)
    boll = BollingerBand(bar, 5)

    for i, price in enumerate(quad):
        bar.pushTick(price, i)
    assert boll.width - 274.36253388 < 1e-5


def test_candle_atr():
    bar = CandleBar(4)
    atr = ATR(bar, 5)

    for i, price in enumerate(const):
        bar.pushTick(price, i)
    assert atr == 0

    for i, price in enumerate(lin):
        bar.pushTick(price, i)
    assert atr - 3.9799 < 1e-3


def test_candle_rsi():
    bar = CandleBar(1)
    rsi = RSI(bar, 14)

    for i, price in enumerate(lin):
        bar.pushTick(price, i)
    assert rsi == 100

    rsi = RSI(bar, 14)
    for i, price in enumerate(alt_quad):
        bar.pushTick(price, i)
    assert rsi - 55.48924 < 1e-5


def test_candle_macd():
    bar = CandleBar(1)
    wma1 = WMA(bar, 5)
    wma2 = WMA(bar, 8)
    macd = MACD(wma1, wma2, 3)

    for i, price in enumerate(sine):
        bar.pushTick(price, i)
    assert macd.diff_ma - 0.5843467703997498 < 1e-5


def test_candle_manb():
    bar = CandleBar(5)
    boll = BollingerBand(bar, 5)
    snb = MABollinger(boll, 5)
    for i, price in enumerate(const):
        bar.pushTick(price, i)
    assert snb == 0

def test_candle_diffMACD():
    bar = CandleBar(1)
    wma1 = WMA(bar, 5)
    wma2 = WMA(bar, 8)
    macd = MACD(wma1, wma2, 3)
    diff = Difference(macd, 'diff', 'diff_ma')

    for i, price in enumerate(alt_quad):
        bar.pushTick(price, i)

    assert diff.value - (-70.11296) < 1e-5
    assert diff.diff_ma - (-35.062037) < 1e-5
    assert diff.diff - (-105.175) < 1e-5

if __name__ == '__main__':
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

    run_all_tests()

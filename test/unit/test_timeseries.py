from cryptle.logging import *
from cryptle.metric.base import Candle, Timeseries, MemoryTS, MultivariateTS
from cryptle.aggregator import Aggregator
from cryptle.event import source, on, Bus
from cryptle.metric.timeseries.atr import ATR
from cryptle.metric.timeseries.bollinger import BollingerBand
from cryptle.metric.timeseries.candle import CandleStick
from cryptle.metric.timeseries.difference import Difference
from cryptle.metric.timeseries.ema import EMA
from cryptle.metric.timeseries.kurtosis import Kurtosis
from cryptle.metric.timeseries.macd import MACD
from cryptle.metric.timeseries.pivot import PivotPoints
from cryptle.metric.timeseries.barreturn import BarReturn
from cryptle.metric.timeseries.rsi import RSI
from cryptle.metric.timeseries.sd import SD
from cryptle.metric.timeseries.skewness import Skewness
from cryptle.metric.timeseries.sma import SMA
from cryptle.metric.timeseries.timestamp import Timestamp
from cryptle.metric.timeseries.volatility import Volatility
from cryptle.metric.timeseries.wma import WMA
from cryptle.metric.timeseries.ym import YM

import logging
import math
import time
import sys
import traceback

const = [3 for i in range(1, 100)]
lin = [i for i in range(1, 100)]
quad = [i ** 2 for i in range(1, 100)]
alt_quad = [(100 + ((-1) ** i) * (i / 4) ** 2) for i in range(1, 100)]
alt_quad_1k = [(100 + ((-1) ** i) * (i / 4) ** 2) for i in range(1, 1000)]
logistic = [(10 / (1 + 100 * math.exp(-i / 10))) for i in range(1, 100)]
sine = [
    (100) + (1 / 4) * (2 * math.sin(i) ** 3 * i - math.sin(i) ** 5) / 2 / (i / 1.5)
    for i in range(1, 100)
]
bars = [
    [1, 3, 4, 0, 0, 0],
    [2, 4, 5, 1, 1, 7],
    [6, 6, 6, 6, 2, 8],
    [1, 3, 4, 0, 0, 0],
    [2, 4, 5, 1, 1, 7],
    [6, 6, 6, 6, 2, 8],
] * 100


@source('tick')
def pushTick(tick):
    return tick


@source('candle')
def pushCandle(bar):
    return bar


def pushSeries(series):
    for i, price in enumerate(series):
        pushTick([price, i, 0, 0])


def pushAltQuad(ts=None):
    for i, price in enumerate(alt_quad):
        pushTick([price, i, 0, 0])


def compare(obj, val, threshold=1e-7):
    assert abs(obj - val) < threshold


def test_candle():
    bus = Bus()
    stick = CandleStick(1)
    aggregator = Aggregator(1)  # set to be a 1 second aggregator
    stick = CandleStick(1)

    bus.bind(aggregator)
    bus.bind(stick)
    bus.bind(pushCandle)

    for i, bar in enumerate(bars):
        pushCandle([*bar, 0])

    assert stick._ts[-1] == [6, 6, 6, 6, 2, 8, 0]


def bind(bus, stick_period=3, aggregator_period=3):
    stick = CandleStick(stick_period)
    aggregator = Aggregator(aggregator_period)
    bus.bind(pushTick)
    bus.bind(stick)
    bus.bind(aggregator)
    return bus, stick


# decorator for testing timeseries.value after looping through alt_quad
def val(func):
    def decorator():
        bus = Bus()
        bus, stick = bind(bus)
        ma, val = func(stick)

        for i, price in enumerate(alt_quad):
            pushTick([price, i, 0, 0])
        compare(ma, val)

    return decorator


@val
def test_sma(stick):
    ma = SMA(stick.o, 5)
    return ma, 197.475


@val
def test_wma(stick):
    ma = WMA(stick.o, 5)
    return ma, 210.675


@val
def test_recursive(stick):
    ma = SMA(WMA(stick.o, 5), 3)
    return ma, 134.65416666666666


@val
def test_ema(stick):
    ma = EMA(stick.o, 5)
    return ma, 213.260999989917483


@val
def test_rsi(stick):
    rsi = RSI(stick.o, 5)
    # not checked
    return rsi, 57.342237492321196


def test_bollinger():
    bus = Bus()
    bus, stick = bind(bus, 1, 1)

    bollinger = BollingerBand(stick.o, 5)
    pushAltQuad()

    compare(bollinger.upperband, 1344.7345184202045)
    compare(bollinger.lowerband, -914.1845184202044)


def test_macd():
    bus = Bus()
    bus, stick = bind(bus, 1, 1)

    wma5 = WMA(stick.o, 5)
    wma8 = WMA(stick.o, 8)
    macd = MACD(wma5, wma8, 3)
    pushAltQuad()

    compare(macd.diff, 52.04722222222)
    compare(macd.diff_ma, 17.350925925907)
    compare(macd.signal, 52.04722222222- 17.350925925907)


def test_atr():
    bus = Bus()
    bus.bind(pushCandle)
    aggregator = Aggregator(5)
    stick = CandleStick(5)
    atr = ATR(stick, 5)
    for i, bar in enumerate(bars):
        pushCandle([*bar, 0])


@val
def test_kurtosis(stick):
    kurt = Kurtosis(stick.o, 5)
    return kurt, -3.231740264178196


@val
def test_skewness(stick):
    skew = Skewness(stick.o, 5)
    return skew, -0.582459640454958


@val
def test_volatility(stick):
    sd = SD(stick.o, 5)
    return sd, 0.00187307396323


@val
def test_return(stick):
    r = BarReturn(stick.o, stick.c, 5, all_close=True)
    return r, 986.0625

@val
def test_ym(stick):
    r = BarReturn(stick.o, stick.c)
    ym = YM(r)
    return ym, 0

@val
def test_diff(stick):
    sd = SD(stick.o, 5)
    diff = Difference(sd)
    return diff, -1.335580558397 * 1e-4


def test_TimeseriesWrapperRetrieval():
    bus = Bus()
    bus, stick = bind(bus, 1, 1)

    diff = Difference(stick.o, 1)
    pushAltQuad()

    assert diff[-21:-19] == [750.8125, -770.3125]
    assert diff[-9] == 1001.3125
    compare(diff, 1188.3125)


def test_MultivariateTSCache():
    bus = Bus()
    bus, stick = bind(bus, 1, 1)

    bollinger = BollingerBand(stick.o, 5)
    wma = WMA(stick.o, 7)

    class MockTS(Timeseries):
        def __repr__(self):
            return self.name
        def __init__(self, lookback, wma, bollinger, name='mock'):
            self.name = name
            self._ts = wma, bollinger
            self._cache = []
            self._lookback = lookback
            self.value = name
            super().__init__(wma, bollinger)

        @MemoryTS.cache('normal')
        def evaluate(self):
            print('obj {} Calling evaluate in MockTS', type(self))

    mock = MockTS(10, wma, bollinger)
    pushAltQuad()

    assert len(mock._cache) == 10
    assert mock._cache[-1] == [
        185.77678571428572,
        -914.1845184202044,
        1344.7345184202045,
        -247.0966190440449,
        564.7297592101022,
    ]


# @Deprecated - use Time event instead of a Timeseries where possible
# def testTimestamp():
#    print('***TESTING TIMESERIES***')
#    bus = Bus()
#    bus.bind(pushTick)
#    aggregator = Aggregator(10) # set to be a 1 second aggregator
#    timestamp = Timestamp(5) # to be implemented
#    bus.bind(aggregator)
#    bus.bind(timestamp)
#
#    for i, price in enumerate(alt_quad):
#        pushTick([price, i, 0, 0])
#    assert timestamp - 80 < 1e-7

# skipped because of this is running suscipiously long
# def testPivotPoints():
#    bus = Bus()
#    bus.bind(pushTick)
#    aggregator = Aggregator(3600)
#    stick = CandleStick(3600)
#    timestamp = Timestamp(5)

#    bus.bind(aggregator)
#    bus.bind(stick)
#    bus.bind(timestamp)

#    pivot = PivotPoints(timestamp, 3600, stick.h, stick.l, stick.c)
#
#    for i, price in enumerate(alt_quad_1k):
#        pushTick([price, i, 0, 0])
#
#    assert pivot.pp -15687.9791666666667 < 1e-7
#    assert pivot.r[2] - 108892.041666667 < 1e-7
#    assert pivot.s[2] - -77516.083333333 < 1e-7

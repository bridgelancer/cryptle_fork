from cryptle.logging import *
from cryptle.metric.base import Candle, Timeseries, TimeseriesWrapper, HistoricalTS
from cryptle.aggregator import Aggregator
from cryptle.event import source, on, Bus
from cryptle.metric.timeseries.atr import ATR
from cryptle.metric.timeseries.bollinger import BollingerBand
from cryptle.metric.timeseries.candle  import CandleStick
from cryptle.metric.timeseries.difference import Difference
from cryptle.metric.timeseries.ema import EMA
from cryptle.metric.timeseries.kurtosis import Kurtosis
from cryptle.metric.timeseries.macd import MACD
from cryptle.metric.timeseries.pivot import PivotPoints
from cryptle.metric.timeseries.rsi import RSI
from cryptle.metric.timeseries.sd import SD
from cryptle.metric.timeseries.skewness import Skewness
from cryptle.metric.timeseries.sma import SMA
from cryptle.metric.timeseries.timestamp import Timestamp
from cryptle.metric.timeseries.volatility import Volatility
from cryptle.metric.timeseries.wma import WMA

from functools import wraps
import logging
import math
import time
import sys
import traceback


const        = [3 for i in range(1, 100)]
lin          = [i for i in range(1, 100)]
quad         = [i**2 for i in range(1, 100)]
alt_quad     = [(100 + ((-1) ** i) * (i/4) **2) for i in range(1, 100)]
alt_quad_1k = [(100 + ((-1) ** i) * (i/4) ** 2) for i in range(1, 1000)]
logistic     = [(10 / ( 1 + 100 * math.exp(-i/10))) for i in range(1, 100)]
sine         = [(100) + (1/4) * ( 2* math.sin(i) ** 3 * i - math.sin(i) ** 5) / 2 / (i /1.5) for i in range(1, 100)]
bars         = [[1,3,4,0,0,0], [2,4,5,1,1,7], [6,6,6,6,2,8], [1,3,4,0,0,0], [2,4,5,1,1,7],
        [6,6,6,6,2,8]] * 100

@source('tick')
def pushTick(tick):
    return tick

def test_candle():
    bus = Bus()
    stick = CandleStick(1)
    aggregator = Aggregator(1) # set to be a 1 second aggregator
    stick = CandleStick(1)

    bus.bind(aggregator)
    bus.bind(stick)

    @source('candle')
    def pushCandle(bar):
        return bar

    bus.bind(pushCandle)

    for i, bar in enumerate(bars):
        pushCandle([*bar, 0])

    assert stick._ts[-1] == [6, 6, 6, 6, 2, 8, 0]


def test_sma():
    bus = Bus()
    bus.bind(pushTick)
    aggregator = Aggregator(3) # set to be a 1 second aggregator
    stick = CandleStick(1)
    ma = SMA(stick.o, 5)

    bus.bind(aggregator)
    bus.bind(stick)

    for i, price in enumerate(alt_quad):
        pushTick([price, i, 0, 0])

    assert ma- 197.475 < 1e-7

def test_wma():
    bus = Bus()
    bus.bind(pushTick)
    aggregator = Aggregator(3)
    stick = CandleStick(1)
    ma = WMA(stick.o, 5)

    bus.bind(aggregator)
    bus.bind(stick)

    for i, price in enumerate(alt_quad):
        pushTick([price, i, 0, 0])
    assert ma- 210.675 < 1e-7

def test_recursive():
    bus = Bus()
    bus.bind(pushTick)
    aggregator = Aggregator(3)
    stick = CandleStick(1)

    bus.bind(aggregator)
    bus.bind(stick)

    ma = SMA(WMA(stick.o, 5), 3)
    for i, price in enumerate(alt_quad):
        pushTick([price, i, 0, 0])
    assert ma- 139.2208333333 < 1e-7

def test_ema():
    bus = Bus()
    bus.bind(pushTick)
    aggregator = Aggregator(1) # set to be a 1 second aggregator
    stick = CandleStick(1)

    bus.bind(aggregator)
    bus.bind(stick)

    ma = EMA(stick.o, 5)
    for i, price in enumerate(alt_quad):
        pushTick([price, i, 0, 0])
    assert ma- 221.029 < 1e-7

def test_bollinger():
    bus = Bus()
    bus.bind(pushTick)
    aggregator = Aggregator(1) # set to be a 1 second aggregator
    stick = CandleStick(1)

    bus.bind(aggregator)
    bus.bind(stick)

    bollinger = BollingerBand(stick.o, 5)
    for i, price in enumerate(alt_quad):
        pushTick([price, i, 0, 0])

    assert bollinger.upperband -  1344.7345184202045 < 1e-7
    assert bollinger.lowerband -  (-914.1845184202044) < 1e-7


def test_rsi():
    bus = Bus()
    bus.bind(pushTick)
    aggregator = Aggregator(3) # set to be a 1 second aggregator
    stick = CandleStick(1)

    bus.bind(aggregator)
    bus.bind(stick)

    rsi = RSI(stick.o, 5)
    for i, price in enumerate(alt_quad_1k):
        pushTick([price, i, 0, 0])

    assert rsi - 61.8272076519321  < 1e-7


def test_macd():
    bus = Bus()
    bus.bind(pushTick)
    aggregator = Aggregator(1)
    stick = CandleStick(1)

    bus.bind(aggregator)
    bus.bind(stick)

    wma5  = WMA(stick.o, 5)
    wma8  = WMA(stick.o, 8)
    macd  = MACD(wma5, wma8, 3)

    for i, price in enumerate(alt_quad):
        pushTick([price, i, 0, 0])
    assert macd.diff - 52.04722222222 < 1e-7
    assert macd.diff_ma -17.7111111111 < 1e-7
    assert macd.signal - 34.696296296296 < 1e-7

def test_atr():
    @source('candle')
    def pushCandle(bar):
        return bar
    bus = Bus()
    bus.bind(pushCandle)
    aggregator = Aggregator(5)
    stick = CandleStick(5)
    atr = ATR(stick, 5)
    for i, bar in enumerate(bars):
        pushCandle([*bar, 0])

def test_kurtosis():
    bus = Bus()
    bus.bind(pushTick)
    aggregator = Aggregator(3) # set to be a 1 second aggregator
    stick = CandleStick(1)

    bus.bind(aggregator)
    bus.bind(stick)

    kurt = Kurtosis(stick.o, 5)
    for i, price in enumerate(alt_quad):
        pushTick([price, i, 0, 0])
    assert kurt- -3.231740264178196 < 1e-5

def test_skewness():
    bus = Bus()
    bus.bind(pushTick)
    aggregator = Aggregator(3) # set to be a 1 second aggregator
    stick = CandleStick(1)

    bus.bind(aggregator)
    bus.bind(stick)

    skew = Skewness(stick.o, 5)
    for i, price in enumerate(alt_quad):
        pushTick([price, i, 0, 0])
    assert skew- -0.582459640454958 < 1e-5

def test_volatility():
    bus = Bus()
    bus.bind(pushTick)
    aggregator = Aggregator(3) # set to be a 1 second aggregator #    stick = CandleStick(1) #    sd = SD(stick.o, 5)
    stick = CandleStick(1)

    bus.bind(aggregator)
    bus.bind(stick)

    sd = SD(stick.o, 5)
    for i, price in enumerate(alt_quad):
        pushTick([price, i, 0, 0])
    assert sd- 0.00187307396323 < 1e-7


def test_diff():
    bus = Bus()
    bus.bind(pushTick)
    aggregator = Aggregator(1) # set to be a 1 second aggregator
    stick = CandleStick(1)

    bus.bind(aggregator)
    bus.bind(stick)

    sd = SD(stick.o, 5)
    diff = Difference(sd)
    for i, price in enumerate(alt_quad):
        pushTick([price, i, 0, 0])
    assert diff- -3.2466947194 * 1e-5 < 1e-7


def test_TimeseriesWrapperRetrieval():
    bus = Bus()
    bus.bind(pushTick)
    aggregator = Aggregator(1) # set to be a 1 second aggregator
    stick = CandleStick(1)

    bus.bind(aggregator)
    bus.bind(stick)

    sd = Difference(stick.o, 1)
    sd_w = TimeseriesWrapper(sd, store_num=10)
    for i, price in enumerate(alt_quad):
        pushTick([price, i, 0, 0])


    assert sd_w[-21:-19] == [750.8125, -770.3125]
    assert sd_w[-9] == 1001.3125

# @Deprecated - use Time event instead of a Timeseries where possible
#def testTimestamp():
#    print('***TESTING TIMESERIES***')
#    bus = Bus()
#    bus.bind(pushTick)
#    aggregator = Aggregator(10) # set to be a 1 second aggregator
#    timestamp = Timestamp(5) # to be implemented
#    bus.bind(aggregator)
#    bus.bind(timestamp)
#
#    for i, price in enumerate(alt_quad):
#        pushTick([price, 0, i, 0])
#    assert timestamp - 80 < 1e-7

# skipped because of this running suscipiously long
#def testPivotPoints():
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

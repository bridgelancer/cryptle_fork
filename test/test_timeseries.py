from cryptle.logging import *
from metric.base import Candle, Timeseries, TimeseriesWrapper, HistoricalTS
from metric.candle import CandleBar
from cryptle.aggregator import Aggregator
from cryptle.event import source, on, Bus
from metric.timeseries.atr import ATR
from metric.timeseries.bollinger import BollingerBand
from metric.timeseries.candle  import CandleStick
from metric.timeseries.difference import Difference
from metric.timeseries.ema import EMA
from metric.timeseries.ichimoku import IchimokuCloud
from metric.timeseries.kurtosis import Kurtosis
from metric.timeseries.macd import MACD
from metric.timeseries.pivot import PivotPoints
from metric.timeseries.rsi import RSI
from metric.timeseries.sd import SD
from metric.timeseries.skewness import Skewness
from metric.timeseries.sma import SMA
from metric.timeseries.timestamp import Timestamp
from metric.timeseries.volatility import Volatility
from metric.timeseries.williamR import WilliamPercentR
from metric.timeseries.wma import WMA

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
alt_quad_10k = [(100 + ((-1) ** i) * (i/4) ** 2) for i in range(1, 100)]
logistic     = [(10 / ( 1 + 100 * math.exp(-i/10))) for i in range(1, 100)]
sine         = [(100) + (1/4) * ( 2* math.sin(i) ** 3 * i - math.sin(i) ** 5) / 2 / (i /1.5) for i in range(1, 100)]
bars         = [[1,3,4,0,0,0], [2,4,5,1,1,7], [6,6,6,6,2,8], [1,3,4,0,0,0], [2,4,5,1,1,7],
        [6,6,6,6,2,8]] * 100

#def test_candle():
#    stick = CandleStick(1)
#
#    @source('candle')
#    def pushCandle(bar):
#        return bar
#
#    bus = Bus()
#    bus.bind(pushCandle)
#    bus.bind(aggregator)
#    bus.bind(stick)
#
#    for i, bar in enumerate(bars):
#        pushCandle([*bar, 0])
#
#    assert stick._ts[-1] == [6, 6, 6, 6, 2, 8, 0]

@source('tick')
def pushTick(tick):
    return tick

#def test_sma():
#    bus = Bus()
#    bus.bind(pushTick)
#    aggregator = Aggregator(1, bus=bus) # set to be a 1 second aggregator
#    stick = CandleStick(1, bus=bus)
#    ma = SMA(stick, 5)
#
#    for i, price in enumerate(alt_quad):
#        pushTick([price, 0, i, 0])
#    assert ma.value - 17.6875 < 1e-7

#def test_wma():
#    bus = Bus()
#    bus.bind(pushTick)
#    aggregator = Aggregator(1, bus=bus) # set to be a 1 second aggregator
#    stick = CandleStick(1, bus=bus)
#    ma = WMA(stick, 5)
#    for i, price in enumerate(alt_quad):
#        pushTick([price, 0, i, 0])
#    assert ma.value - 22.5375 < 1e-7

#def test_recursive():
#    bus = Bus()
#    bus.bind(pushTick)
#    aggregator = Aggregator(1, bus=bus) # set to be a 1 second aggregator
#    stick = CandleStick(1, bus=bus)
#    ma = SMA(WMA(stick, 5), 3)
#    for i, price in enumerate(alt_quad):
#        pushTick([price, 0, i, 0])
#    assert ma.value - 59.9666667 < 1e-7

#def test_ema():
#    bus = Bus()
#    bus.bind(pushTick)
#    aggregator = Aggregator(1, bus=bus) # set to be a 1 second aggregator
#    stick = CandleStick(1, bus=bus)
#    ma = EMA(stick, 5)
#    for i, price in enumerate(alt_quad):
#        pushTick([price, 0, i, 0])
#    assert ma.value - -23.5015 < 1e-7

def test_bollinger():
    bus = Bus()
    bus.bind(pushTick)
    aggregator = Aggregator(1, bus=bus) # set to be a 1 second aggregator
    stick = CandleStick(1, bus=bus)
    bollinger = BollingerBand(stick, 5)
    for i, price in enumerate(alt_quad):
        pushTick([price, 0, i, 0])

    assert bollinger.upperband -  1271.5142485395759 < 1e-7
    assert bollinger.lowerband - -1306.8892485395759 < 1e-7
#
#def test_rsi():
#    bus = Bus()
#    bus.bind(pushTick)
#    aggregator = Aggregator(1, bus=bus) # set to be a 1 second aggregator
#    stick = CandleStick(1, bus=bus)
#    rsi = RSI(stick, 5)
#    for i, price in enumerate(alt_quad):
#        pushTick([price, 0, i, 0])
#
#def test_macd():
#    bus = Bus()
#    bus.bind(pushTick)
#    aggregator = Aggregator(1, bus=bus)
#    stick = CandleStick(1, bus=bus)
#
#    wma5  = WMA(stick.o, 5)
#    wma8  = WMA(stick.o, 8)
#    macd  = MACD(wma5, wma8, 3)
#
#    for i, price in enumerate(alt_quad):
#        pushTick([price, 0, i, 0])
#    assert macd.diff - -53.127777777 < 1e-7
#    assert macd.diff_ma -17.7111111111 < 1e-7
#    assert macd.value - 34.696296296296 < 1e-7
#
#def test_difference():
#    bus = Bus()
#    bus.bind(pushTick)
#    aggregator = Aggregator(1, bus=bus)
#    stick = CandleStick(1, bus=bus)
#
#    diff  = Difference(stick.o)
#    for i, price in enumerate(alt_quad):
#        pushTick([price, 0, i, 0])
#    assert diff - -1212.8125 < 1e-3
#
#def test_atr():
#    @source('candle')
#    def pushCandle(bar):
#        return bar
#    bus = Bus()
#    bus.bind(pushCandle)
#    aggregator = Aggregator(5, bus=bus)
#    stick = CandleStick(5, bus=bus)
#    atr = ATR(stick, 5)
#    for i, bar in enumerate(bars):
#        pushCandle([*bar, 0])
#
#def test_kurtosis():
#    bus = Bus()
#    bus.bind(pushTick)
#    aggregator = Aggregator(1, bus=bus) # set to be a 1 second aggregator
#    stick = CandleStick(1, bus=bus)
#    kurt = Kurtosis(stick, 5)
#    for i, price in enumerate(alt_quad):
#        pushTick([price, 0, i, 0])
#    assert kurt.value - -3.323900651 < 1e-5
#
#def test_skewness():
#    bus = Bus()
#    bus.bind(pushTick)
#    aggregator = Aggregator(1, bus=bus) # set to be a 1 second aggregator
#    stick = CandleStick(1, bus=bus)
#    skew = Skewness(stick, 5)
#    for i, price in enumerate(alt_quad):
#        pushTick([price, 0, i, 0])
#    assert skew.value - 0.60615850445 < 1e-5
#
## not validated - forgotten formula
#def test_williamR():
#    bus = Bus()
#    bus.bind(pushTick)
#    aggregator = Aggregator(1, bus=bus) # set to be a 1 second aggregator
#    stick = CandleStick(1, bus=bus)
#    william = WilliamPercentR(stick, 5)
#    for i, price in enumerate(alt_quad):
#        pushTick([price, 0, i, 0])
#
#def test_volatility():
#    bus = Bus()
#    bus.bind(pushTick)
#    aggregator = Aggregator(1, bus=bus) # set to be a 1 second aggregator
#    stick = CandleStick(1, bus=bus)
#    sd = SD(stick, 5)
#    for i, price in enumerate(alt_quad):
#        pushTick([price, 0, i, 0])
#    assert sd.value - 0.0015513475 < 1e-7
#
#def test_diff():
#    bus = Bus()
#    bus.bind(pushTick)
#    aggregator = Aggregator(1, bus=bus) # set to be a 1 second aggregator
#    stick = CandleStick(1, bus=bus)
#    sd = SD(stick, 5)
#    diff = Difference(sd)
#    for i, price in enumerate(alt_quad):
#        pushTick([price, 0, i, 0])
#    assert diff.value - -3.2466947194 * 1e-5 < 1e-7
#
#def test_TimeseriesWrapperRetrieval():
#    bus = Bus()
#    bus.bind(pushTick)
#    aggregator = Aggregator(1, bus=bus) # set to be a 1 second aggregator
#    stick = CandleStick(1, bus=bus)
#    sd = Difference(stick.o, 1)
#    sd_w = TimeseriesWrapper(sd, store_num=10)
#    for i, price in enumerate(alt_quad):
#        pushTick([price, 0, i, 0])
#
#    assert sd_w[-21:-19] == [750.8125, -770.3125]
#    assert sd_w[-9] == 1001.3125

#def testTimestamp():
#    print('***TESTING TIMESERIES***')
#    bus = Bus()
#    bus.bind(pushTick)
#    aggregator = Aggregator(1, bus=bus) # set to be a 1 second aggregator
#    timestamp = Timestamp(5, bus=bus) # to be implemented
#
#    for i, price in enumerate(alt_quad):
#        print(i, price)
#        pushTick([price, 0, i, 0])
#        try:
#            print('timestamp passed: ', float(timestamp))
#            pass
#        except:
#            pass
#

def testPivotPoints():
    bus = Bus()
    bus.bind(pushTick)
    aggregator = Aggregator(3600, bus=bus) # set to be a 1 second aggregator
    stick = CandleStick(3600, bus=bus)
    timestamp = Timestamp(5, bus=bus) # to be implemented
    pivot = PivotPoints(timestamp, 3600, stick.h, stick.l, stick.c,)
    for i, price in enumerate(alt_quad):
        pushTick([price, 0, i*3600 + 1, 0])
        print(timestamp.value, stick.h, stick.l, stick.c, (timestamp.value + 3600) / 3600)
        try:
            print("Pivot point", pivot, pivot.r, pivot.s)
            #print("Pivot point", pivot, "\n")
            #print("Supports:", pivot.s[:4])
            #print("Resistances:", pivot.r[:4], "\n")
        except:
            pass

def test_hisotiralTS():
    pass

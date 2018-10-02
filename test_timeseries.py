from cryptle.loglevel import *
from metric.base import Candle, Timeseries
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
from metric.timeseries.rsi import RSI
from metric.timeseries.sd import SD
from metric.timeseries.skewness import Skewness
from metric.timeseries.sma import SMA
from metric.timeseries.volatility import Volatility
from metric.timeseries.williamR import WilliamPercentR
from metric.timeseries.wma import WMA

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

fh = logging.FileHandler('timeseriestest.log', mode='w')
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)

logger = logging.getLogger('Timeseries')
logger.setLevel(logging.DEBUG)
logger.addHandler(sh)
logger.addHandler(fh)

const        = [3 for i in range(1, 100)]
lin          = [i for i in range(1, 100)]
quad         = [i**2 for i in range(1, 100)]
alt_quad     = [(100 + ((-1) ** i) * (i/4) **2) for i in range(1, 100)]
alt_quad_10k = [(100 + ((-1) ** i) * (i/4) ** 2) for i in range(1, 100)]
logistic     = [(10 / ( 1 + 100 * math.exp(-i/10))) for i in range(1, 100)]
sine         = [(100) + (1/4) * ( 2* math.sin(i) ** 3 * i - math.sin(i) ** 5) / 2 / (i /1.5) for i in range(1, 100)]
bars         = [[1,3,4,0,0,0], [2,4,5,1,1,7], [6,6,6,6,2,8]]


def test_candle():
    c = Candle(4, 7, 10, 3, 12316, 1, 1)
    assert c.open == 4
    assert c.close == 7
    assert c.high == 10
    assert c.low == 3
    assert c.timestamp == 12316
    assert c.volume == 1
    assert c.netvol == 1


def test_candlestick():
    # CandleStick converts barseries to appropriate form
    # Barseries is an object with gives out constantly updating bars
    # upon update, the onCandle function of the CandleStick class would be invoked
    aggregator = Aggregator(1) # set to be a 1 second  aggregator
    stick = CandleStick(1)

    @source('candle')
    def pushCandle(bar):
        return bar

    bus = Bus()
    bus.bind(pushCandle)
    bus.bind(aggregator)
    bus.bind(stick)

    for i, bar in enumerate(bars):
        pushCandle([*bar, 0])

    assert stick._ts[-1] == [6, 6, 6, 6, 2, 8, 0]

@source('tick')
def pushTick(tick):
    return tick

def test_sma():

    bus = Bus()
    bus.bind(pushTick)
    aggregator = Aggregator(1, bus=bus) # set to be a 1 second aggregator
    stick = CandleStick(1, bus=bus)
    ma = SMA(stick, 5, name='fuck')

    for i, price in enumerate(alt_quad):
        pushTick([price, 0, i, 0])
    assert ma.value - 17.6875 < 1e-7

def test_wma():
    bus = Bus()
    bus.bind(pushTick)
    aggregator = Aggregator(1, bus=bus) # set to be a 1 second aggregator
    stick = CandleStick(1, bus=bus)
    ma = WMA(stick, 5)
    for i, price in enumerate(alt_quad):
        pushTick([price, 0, i, 0])
    assert ma.value - 22.5375 < 1e-7

def test_recursive():
    bus = Bus()
    bus.bind(pushTick)
    aggregator = Aggregator(1, bus=bus) # set to be a 1 second aggregator
    stick = CandleStick(1, bus=bus)
    ma = SMA(WMA(stick, 5), 3)
    for i, price in enumerate(alt_quad):
        pushTick([price, 0, i, 0])
    assert ma.value - 59.9666667 < 1e-7

def test_ema():
    bus = Bus()
    bus.bind(pushTick)
    aggregator = Aggregator(1, bus=bus) # set to be a 1 second aggregator
    stick = CandleStick(1, bus=bus)
    ma = EMA(stick, 5)
    for i, price in enumerate(alt_quad):
        pushTick([price, 0, i, 0])
    assert ma.value - -23.5015 < 1e-7

def test_bollinger():
    bus = Bus()
    bus.bind(pushTick)
    aggregator = Aggregator(1, bus=bus) # set to be a 1 second aggregator
    stick = CandleStick(1, bus=bus)
    bollinger = BollingerBand(stick, 5)
    for i, price in enumerate(alt_quad):
        pushTick([price, 0, i, 0])

    assert float(bollinger._upperband) - 1271.5142485395759 < 1e-7
    assert float(bollinger._lowerband) - -1306.8892485395759 < 1e-7

#def test_rsi():
#    pass
#
#def test_macd():
#    pass

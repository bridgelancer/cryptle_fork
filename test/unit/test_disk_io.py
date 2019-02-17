from cryptle.logging import *
from cryptle.metric.base import Candle, Timeseries, MemoryTS, MultivariateTS, DiskTS
from cryptle.metric.timeseries.sma import SMA
from cryptle.metric.timeseries.candle import CandleStick
from cryptle.aggregator import Aggregator
from cryptle.event import source, Bus

import pytest
import os

alt_quad = [(100 + ((-1) ** i) * (i / 4) ** 2) for i in range(1, 1000)]

@source('tick')
def pushTick(tick):
    return tick

def pushAltQuad():
    for i, price in enumerate(alt_quad):
        pushTick([price, i, 0, 0])

stick = CandleStick(1)
aggregator = Aggregator(1)

sma = SMA(stick.o, 7)

bus = Bus()
bus.bind(aggregator)
bus.bind(stick)
bus.bind(pushTick)

pushAltQuad()

@pytest.mark.skip()
def test_file_construction():
    pass

@pytest.mark.skip()
def test_time():
    pass

@pytest.mark.skip()
def test_id():
    pass

@pytest.mark.skip()
def test_clean_up():
    pass

@pytest.mark.skip()
def test_multiple_bus():
    pass

dirlist = [d for d in os.listdir('./histlog')]

for directory in dirlist:
    for file in [f for f in os.listdir(os.path.join('./histlog', directory))]:
        os.remove(os.path.join('./histlog', directory, file))
    os.rmdir(os.path.join('./histlog', directory))


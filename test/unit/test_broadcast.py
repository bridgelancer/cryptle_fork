from cryptle.logging import *
from cryptle.metric.base import Candle, Timeseries, MemoryTS, MultivariateTS, GenericTS
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
import pytest
from datetime import datetime

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

def bind(bus, stick_period=3, aggregator_period=3):
    stick = CandleStick(stick_period)
    aggregator = Aggregator(aggregator_period)
    bus.bind(pushTick)
    bus.bind(stick)
    bus.bind(aggregator)
    return bus, stick

def test_naive_integration():
    pass


def test_same_episode():
    stick_period = aggregator_period = 300

    int_t1 = 1549544100
    t1 = datetime.fromtimestamp(1549544100).time()
    t2 = datetime.fromtimestamp(int_t1 + 900).time()
    t3 = datetime.fromtimestamp(int_t1 - 300).time()
    t4 = datetime.fromtimestamp(int_t1 - 600).time()
    t5 = datetime.fromtimestamp(int_t1 + 1500).time()
    t6 = datetime.fromtimestamp(int_t1 + 3000).time()

    bus = Bus()
    candle = CandleStick(stick_period)
    timestamp = Timestamp(stick_period)
    aggregator = Aggregator(aggregator_period)

    bus.bind(pushTick)
    bus.bind(timestamp)
    bus.bind(candle)
    bus.bind(aggregator)

    def start_to_entry_vol_f(v, ts):
        if ts == 1549544100 or ts == int_t1 + 300 or ts == int_t1 + 900:
            return sum(v._cache[-3:])

    start_to_entry_vol = GenericTS(
        candle.v,
        timestamp,
        name='start_to_entry_vol',
        lookback=6,
        eval_func=start_to_entry_vol_f,
        args=[candle.v, timestamp],
        tocache=True,
    )

    def foo_f(start_to_entry_vol, o):
        print('returning')
        return -1

    foo = GenericTS(
        start_to_entry_vol,
        candle.o,
        name='foo',
        lookback=6,
        eval_func=foo_f,
        args=[candle.o, start_to_entry_vol],
        tocache=True,
        update_mode='concurrent',
    )

    for i, price in enumerate(alt_quad):
        pushTick([price, 1549524600 + 300 * i, 0, 0])


def test_by_timestamp():
    pytest.skip('Not implemented for the moment')


def test_num_of_broadcasts():
    pytest.skip('Not implemented for the moment')

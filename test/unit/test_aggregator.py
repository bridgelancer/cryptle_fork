from cryptle.metric.timeseries.sma import SMA
from cryptle.metric.timeseries.wma import WMA
from cryptle.metric.timeseries.candle import CandleStick
from cryptle.metric.timeseries.difference import Difference
from cryptle.aggregator import DecoratedAggregator, Aggregator
from cryptle.event import source, Bus

import pytest

"""Test module for testing function of Aggregator and DecoratedAggregator"""

# loop till 999 for allowing caching to occur
alt_quad = [(100 + ((-1) ** i) * (i / 4) ** 2) for i in range(1, 1000)]


@source('tick')
def pushTick(tick):
    return tick


def pushAltQuad():
    for i, price in enumerate(alt_quad):
        pushTick([price, i, 0, 0])


@pytest.fixture(scope='module')
def data_pushing():
    stick = CandleStick(1)
    aggregator = DecoratedAggregator(1)
    sma = SMA(stick.o, 7)

    bus = Bus()
    bus.bind(aggregator)
    bus.bind(stick)
    bus.bind(pushTick)

    pushAltQuad()
    return sma, stick


@pytest.fixture
def primary_ts(data_pushing):
    """Return the Timeseries objects with cache written for checking"""
    sma, stick = data_pushing
    return (sma, stick.o, stick.c, stick.h, stick.l, stick.v)


def test_push_init_candle():
    pass


def test_push_full_candle():
    pass


def test_push_empty_candle():
    pass


def test_pushTick():
    pass


def test_emit_aggregated_candle():
    pass


def test_emit_full_candle():
    pass


def test_push_all_metrics():
    pass

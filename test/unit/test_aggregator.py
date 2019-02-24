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
    aggregator = DecoratedAggregator(5)

    bus = Bus()
    bus.bind(aggregator)
    bus.bind(pushTick)

    return aggregator


@pytest.fixture
def primary_ts(data_pushing):
    """Return the Timeseries objects with cache written for checking"""
    sma, stick = data_pushing
    return (sma, stick.o, stick.c, stick.h, stick.l, stick.v)


def test_push_init_candle():
    """Testing the side effects of _pushInitCandle method of Aggregator"""
    aggregator = Aggregator(1)
    bar = aggregator._pushInitCandle(10, 1, 0, 0)
    assert bar is None
    assert len(aggregator._bars) == 1

    # Always return second-last candle, the most recent finished bar
    bar = aggregator._pushInitCandle(20, 1, 0, 0)
    assert bar == aggregator._bars[0]._bar
    assert len(aggregator._bars) == 2


def test_push_tick():
    """Asserting aggregation correctness for each tick pushed"""
    n = 5
    aggregator = Aggregator(n)

    for i, price in enumerate(alt_quad):
        for bar in aggregator.pushTick([price, i, 0, 0]):
            if bar is None:
                assert len(aggregator._bars) == 1
            else:
                assert bar == aggregator._bars[i//n - 1]._bar
                assert len(aggregator._bars) == i // n + 1

                assert aggregator.last_low == min(alt_quad[i - i%n:i+1])
                assert aggregator.last_high == max(alt_quad[i - i%n:i+1])
                assert aggregator.last_open == alt_quad[i- i%n]
                assert aggregator.last_close == alt_quad[i]


def test_push_tick_with_empty_bars():
    n = 5
    q = 4
    aggregator = Aggregator(n)

    alt_quad_shortened = alt_quad[::n*q]

    for i, price in enumerate(alt_quad_shortened):
        for num, bar in enumerate(aggregator.pushTick([price, i*n*q, 0, 0])):
            if bar is None:
                assert len(aggregator._bars) == 1
            else:
                old_price = alt_quad_shortened[i-1]
                if num != q-1:
                    assert aggregator.last_open == alt_quad_shortened[i-1]
                else:
                    assert aggregator.last_open == alt_quad_shortened[i]


def test_emit_aggregated_candle(data_pushing):
    n = 5
    # getting the aggregator implementation
    aggregator = data_pushing.aggregator

    for i, price in enumerate(alt_quad):
        pushTick([price, i, 0, 0])
        assert len(aggregator._bars) == i // n + 1

        assert aggregator.last_low == min(alt_quad[i - i%n:i+1])
        assert aggregator.last_high == max(alt_quad[i - i%n:i+1])
        assert aggregator.last_open == alt_quad[i- i%n]
        assert aggregator.last_close == alt_quad[i]

@pytest.mark.skip(reason='not implemented')
def test_emitAllMetrics():
    pass


@pytest.mark.skip(reason='not implemented')
def test_emit_order():
    pass

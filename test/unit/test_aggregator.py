from cryptle.metric.timeseries.sma import SMA
from cryptle.metric.timeseries.candle import CandleStick
from cryptle.aggregator import DecoratedAggregator, Aggregator
from cryptle.event import source, Bus

import pytest

"""Test module for testing functions of Aggregator and DecoratedAggregator classes"""

# loop till 999 for allowing caching
alt_quad = [(100 + ((-1) ** i) * (i / 4) ** 2) for i in range(1, 1000)]
partial_bars = [(i - 1, i + 2, i + 10, i - 10, i, 0, 0) for i in range(1, 1000)]


@source('tick')
def pushTick(tick):
    return tick


@pytest.fixture(scope='module')
def decorated_aggregator():
    decorated_aggregator = DecoratedAggregator(5)

    bus = Bus()
    bus.bind(decorated_aggregator)
    bus.bind(pushTick)

    return decorated_aggregator


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
    aggregator = Aggregator(n, auto_prune=False)

    for i, price in enumerate(alt_quad):
        for bar in aggregator.pushTick([price, i, 0, 0]):
            if bar is None:
                assert len(aggregator._bars) == 1
            else:
                assert bar == aggregator._bars[i // n - 1]._bar
                assert len(aggregator._bars) == i // n + 1

                assert aggregator.last_low == min(alt_quad[i - i % n : i + 1])
                assert aggregator.last_high == max(alt_quad[i - i % n : i + 1])
                assert aggregator.last_open == alt_quad[i - i % n]
                assert aggregator.last_close == alt_quad[i]


def test_push_tick_with_empty_bars():
    """Asserting the aggregation correctness in empty bar situation"""
    n = 5
    q = 4
    aggregator = Aggregator(n)

    alt_quad_shortened = alt_quad[:: n * q]

    for i, price in enumerate(alt_quad_shortened):
        for num, bar in enumerate(aggregator.pushTick([price, i * n * q, 0, 0])):
            if bar is None:
                assert len(aggregator._bars) == 1
            else:
                old_price = alt_quad_shortened[i - 1]
                if num != q - 1:
                    assert aggregator.last_open == alt_quad_shortened[i - 1]
                else:
                    assert aggregator.last_open == alt_quad_shortened[i]


def test_push_partial_bars():
    """Asserting the aggregation correctness for partial bars"""
    period = 50
    pbar_period = 5
    num_partial_bars = period // pbar_period

    aggregator = Aggregator(period)

    for i, pbar in enumerate(partial_bars):
        for bar in aggregator.pushPartialCandle(pbar):
            print(bar)
            if bar is None:
                assert len(aggregator._bars) == 1
            else:
                assert bar == aggregator._bars[i // period - 1]._bar
                assert len(aggregator._bars) == i // period + 1

                pbs = partial_bars[i - i % period : i + 1]

                assert aggregator.last_low == min([bar[3] for bar in pbs])
                assert aggregator.last_high == max([bar[2] for bar in pbs])
                assert aggregator.last_open == pbs[0][0]
                assert aggregator.last_close == pbs[-1][1]


def test_emit_aggregated_candle(decorated_aggregator):
    """Asserting the bar emission wiring between DecoratedAggregator and Aggregator"""
    n = 5
    # getting the aggregator implementation
    aggregator = decorated_aggregator.aggregator

    for i, price in enumerate(alt_quad):
        pushTick([price, i, 0, 0])
        assert len(aggregator._bars) <= 100

        assert aggregator.last_low == min(alt_quad[i - i % n : i + 1])
        assert aggregator.last_high == max(alt_quad[i - i % n : i + 1])
        assert aggregator.last_open == alt_quad[i - i % n]
        assert aggregator.last_close == alt_quad[i]


def test_auto_prune():
    n = 5
    aggregator = Aggregator(n, auto_prune=True, maxsize=20)

    for i, price in enumerate(alt_quad):
        for bar in aggregator.pushTick([price, i, 0, 0]):
            if bar is None:
                assert len(aggregator._bars) == 1
            else:
                assert bar == aggregator._bars[-2]._bar
                assert len(aggregator._bars) <= 20

                assert aggregator.last_low == min(alt_quad[i - i % n : i + 1])
                assert aggregator.last_high == max(alt_quad[i - i % n : i + 1])
                assert aggregator.last_open == alt_quad[i - i % n]
                assert aggregator.last_close == alt_quad[i]


@pytest.mark.skip(reason='not implemented')
def test_emitAllMetrics():
    pass


@pytest.mark.skip(reason='not implemented')
def test_emit_order():
    pass

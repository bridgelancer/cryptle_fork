from cryptle.logging import *
from cryptle.metric.base import Candle, Timeseries, MemoryTS, MultivariateTS, DiskTS
from cryptle.metric.timeseries.sma import SMA
from cryptle.metric.timeseries.wma import WMA
from cryptle.metric.timeseries.candle import CandleStick
from cryptle.metric.timeseries.difference import Difference
from cryptle.aggregator import Aggregator
from cryptle.event import source, Bus

import pytest
import os
from pathlib import Path
from enum import Enum
import datetime

alt_quad = [(100 + ((-1) ** i) * (i / 4) ** 2) for i in range(1, 1000)]

"""Test module for testing the IO operation of DiskTS

Note:
    Prefer to run with -rxXs pytest flag, same applies to other test modules. A minimum of 2 seconds
    is needed between successive testing to avoid collision of directory name. No logs would be
    created after the successful execution of test_remove_files.

"""


@source('tick')
def pushTick(tick):
    return tick


def pushAltQuad():
    for i, price in enumerate(alt_quad):
        pushTick([price, i, 0, 0])


stick = CandleStick(1)
stick2 = CandleStick(1)
aggregator = Aggregator(1)
aggregator2 = Aggregator(1)

sma = SMA(stick.o, 7)
wma = WMA(stick2.o, 7)

bus = Bus()
bus.bind(aggregator)
bus.bind(stick)
bus.bind(pushTick)


pushAltQuad()

histroot = Path.cwd() / Path('histlog')
# Note the similar problem in DiskTS -> spordic discrepancy due to time diff
current_time = datetime.datetime.now()
current_time_f = current_time.strftime('%Y-%m-%d %H:%M:%S')

primary_ts = (sma, stick.o, stick.c, stick.h, stick.l, stick.v)

dirpaths = []
for i in range(-1, 1):
    diff_time = current_time + datetime.timedelta(seconds=i)
    diff_time_f = diff_time.strftime('%Y-%m-%d %H:%M:%S')
    subdirpath = histroot / diff_time_f
    dirpaths.append(Path.cwd() / subdirpath)


def assert_file_exists(ts):
    dpath = None
    try:
        for dirpath in dirpaths:
            if Path.exists(dirpath):
                dpath = dirpath
                break
    except Exception as e:
        raise OSError(
            "Error in creating the required directory for storing DiskTS values."
        )

    path = Path(dpath / f'{repr(ts)}_{id(ts)}.csv')
    assert path.exists()
    return path


def check_end_state(ts):
    assert len(ts.hxtimeseries._cache) == 0
    assert len(ts.hxtimeseries.readCSV([], assert_file_exists(ts))) == 998


def clean_up(ts):
    assert len(ts.hxtimeseries._cache) == 198
    assert len(ts.hxtimeseries.readCSV([], assert_file_exists(ts))) == 800
    ts.hxtimeseries.cleanup()
    check_end_state(ts)


def test_file_construction():
    """Test both the correct number of files generated and the names of the files"""
    dpath = None
    for ts in primary_ts:
        path = assert_file_exists(ts)
        dpath = path

    assert len(sorted(Path(dpath.parent).glob('*'))) == 6


def test_clean_up():
    """Assert the number of elements in file before and after cleaning up"""
    for ts in primary_ts:
        clean_up(ts)


def test_history_retrieval():
    bus = Bus()
    stick = CandleStick(1)
    aggregator = Aggregator(1)
    bus.bind(pushTick)
    bus.bind(stick)
    bus.bind(aggregator)

    diff = Difference(stick.o, 1)

    alt_quad_100 = [(100 + ((-1) ** i) * (i / 4) ** 2) for i in range(1, 100)]

    for i, price in enumerate(alt_quad_100):
        pushTick([price, i, 0, 0])

    assert diff[-21:-19] == [750.8125, -770.3125]
    assert diff[-9] == 1001.3125


# Todo remove xfail mark after Event bus was fixed
@pytest.mark.xfail(reason='Unresolved bugs in Event bus implementation')
def test_multiple_bus():
    bus = Bus()
    bus.bind(aggregator)
    bus.bind(stick)
    bus.bind(pushTick)
    pushAltQuad()

    # Should not affect the state of SMA, known issue documented in xfail reason
    for ts in primary_ts:
        check_end_state(ts)

    # Checking validity of WMA output
    assert_file_exists(wma)
    clean_up(wma)


def test_remove_files():
    ## For cleaning up the directories constructed
    for directory in histroot.iterdir():
        for file in directory.iterdir():
            os.remove(histroot / directory / file)
        Path.rmdir(histroot / directory)

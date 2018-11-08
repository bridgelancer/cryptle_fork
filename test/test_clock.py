import time
import functools

import pytest

from cryptle.clock import Clock
from cryptle.event import Bus


@pytest.fixture
def bus():
    return Bus()


def test_count_seconds(bus):
    class Foo:
        def __init__(self):
            self.count = 0
        def add(self, data=None):
            self.count += 1

    clock = Clock()
    foo = Foo()

    bus.bind(clock)
    bus.addListener('second', foo.add)

    clock.start()
    time.sleep(3)
    clock.stop()
    assert foo.count == 3

def test_second_sensitivity(bus):
    def check_precision(clock, now):
        try:
            # Check that the callback doesn't have too much overhead
            assert now - time.time() < 0.1

            # Check the alignment of the event with real clock time
            assert now % 1 < 0.1
        finally:
            clock.stop()

    clock = Clock()
    bus.bind(clock)
    bus.addListener('second', functools.partial(check_precision, clock))
    clock.start()

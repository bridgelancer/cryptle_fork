import inspect
import json
from datetime import datetime


def appendTimestamp(msg, t):
    return '{} At: {}'.format(msg, datetime.fromtimestamp(t).strftime("%d %H:%M:%S"))


def truncate(f, dp):
    fmt = '{:.' + str(dp) + 'f}'
    s = fmt.format(f)
    return float(s)


def checkType(param, *types):
    valid_type = False

    for t in types:
        valid_type |= isinstance(param, t)

    if not valid_type:
        caller = inspect.stack()[1][3]
        passed = type(param).__name__

        fmt = "{} was passed to {}() where {} is expected"
        msg = fmt.format(passed, caller, types)

        raise TypeError(msg)


# Hardcoded for bitstamp
def unpackTick(tick):
    checkType(tick, dict)

    price = tick['price']
    volume = tick['amount']
    timestamp = float(tick['timestamp'])
    action = 1 - tick['type'] * 2

    return price, timestamp, volume, action


class DirectionFlag:
    '''A boolean which can be accessed with specialised named attritubes.

    The value of this flag can be accessed through members, up/down. The value
    of these attributes are always oppositive of each other.
    '''

    def __init__(self):
        self._up = self._down = False

    @property
    def up(self):
        return self._up

    @property
    def down(self):
        return self._down

    @up.setter
    def up(self, value):
        self._up = value
        self._down = not value

    @down.setter
    def down(self, value):
        self._down = value
        self._up = not value


class IntensityFlag():

    def __init__(self):
        self._high = self._low = False

    def setHigh(self):
        self._high = True
        self._low = False

    def setLow(self):
        self._high = False
        self._low = True

    @property
    def high(self):
        return self._high

    @property
    def low(self):
        return self._low


class TradeFlag:
    '''A boolean which can be accessed with specialised named attritubes.

    The value of this flag can be accessed through members, buy/sell. The value
    of these attributes are always oppositive of each other.
    '''

    def __init__(self):
        self._buy = self._sell = False

    def setBuy(self):
        self._buy = True
        self._sell = False

    def setSell(self):
        self._buy = False
        self._sell = True

    @property
    def buy(self):
        return self._buy

    @property
    def sell(self):
        return self._sell


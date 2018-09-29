# This intends to be the new .py file that contains the wrappers of the respective TimeSeries
# objects

from .candle import *
from .base import TimeSeries
from .generic import *

def Wrapper:
    '''Base class of all the wrapper objects for the new TimeSeries object.

    Wrapper would provide interface to retrieve the updated value of the TimeSeries object. In the
    future, it would also allow access to historical values of the TimeSeries that are stored to
    disk.

    For metrics that hold several TimeSeries objects to comprise a valid Metric in the original
    sense, the Wrapper object should wrap the corresponding TimeSeries. As such, the manifestation
    of a valid Metric is encapsulated in such a Wrapper construct.

    '''
    def getValue(self):
        return self.value

    def getPastHistory(self, lookback):
        raise NotImplementedError

    def getTimeSeries(self):
        return list(self.__dict__.keys())

    def __int__(self):
        return int(self.value)

    def __float__(self):
        return float(self.value)

    def __neg__(self):
        return -self.value

    def __abs__(self):
        return abs(self.value)

    def __repr__(self):
        return str(self.value)

    def __str__(self):
        return str(self.value)

    def __eq__(self, other):
        return self.value == other

    def __ne__(self, other):
        return self.value != other

    def __lt__(self, other):
        return self.value < other

    def __gt__(self, other):
        return self.value > other

    def __ge__(self, other):
        return self.value >= other

    def __le__(self, other):
        return self.value <= other

    def __add__(self, other):
        return self.value + other

    def __sub__(self, other):
        return self.value - other

    def __mul__(self, other):
        return self.value * other

    def __truediv__(self, other):
        return self.value / other

    def __floordiv__(self, other):
        return self.value // other

    def __pow__(self, other):
        return self.value ** other

    def __radd__(self, other):
        return other + self.value

    def __rsub__(self, other):
        return other - self.value

    def __rmul__(self, other):
        return other * self.value

    def __rtruediv__(self, other):
        return other /self.value

    def __rfloordiv__(self, other):
        return other // self.value

    def __rpow__(self, other):
        return other ** self.value


def Candle(Wrapper):

    '''Manifestation of original candle object with open, close, high, low, volume TimeSeries'''

    def __init__(self, o, c, h, l, v):
        self.o = o
        self.c = c
        self.h = h
        self.l = l
        self.v = v
        self.value = 0 # by default, the value will take the open price value

def SMA(Wrapper):

    '''Manifestaion of original SMA object with SMA TimeSeries'''

    def __init__(self, sma):
        self.value = sma

def WMA(Wrapper):

    '''Manifestation of original WMA object with WMA TimeSeries'''

    def __init__(self, wma):
        self.value = sma

def EMA(Wrapper):

    '''Manifestatino of original EMA object with EMA TimeSeries'''

    def __init__(self, ema):
        self.value = ema

def ATR(Wrapper):

    '''Manifestation of original ATR obect with t1, t2, t3, tr TimeSeries'''

    def __init__(self, t1, t2, t3, tr):
        self.t1 = t1
        self.t2 = t2
        self.t3 = t3
        self.tr = tr
        self.value = 0

def MACD(Wrapper):

    '''Manifestation of original MACD object with fast, slow, diff, diff_ma TimeSeries'''

    def __init__(self, diff, diff_ma):
        self.diff = diff
        self.diff_ma = diff_ma
        self.value = self.diff - self.diff_ma

def Difference(Wrapper):

    '''Manifestation of original Difference object with a dictionary of lists of historic n-th
    differences. '''

    def __init__(self, difference):
        self.difference = difference
        self.value = self.difference

def BollingerBand(Wrapper):

    '''Manifestation of original BollingerBand object with width, upperband, lowerband and band Time
    series'''

    def __init__(self, width, upperband, lowerband, band):
        self.width = width
        self.upperband = upperband
        self.lowerband = lowerband
        self.band = band
        self.value = self.band

def RSI(Wrapper):

    '''Manifestation of original RSI object with rsi TimeSeries'''

    def __init__(self, rsi):
        self.rsi = rsi
        self.value = self.rsi

def Volatility(Wrapper):

    '''Manifestation of original Volatility object with volatility TimeSeries'''

    def __init__(self, volatility):
        self.volatility = volatility
        self.value = self.volatility

def Kurtosis(Wrapper):

    '''Manifestation of original Kurtosis object with kurtosis TimeSeries'''

    def __init__(self, kurtosis):
        self.kurtosis = kurtosis
        self.value = self.kurtosis

def Skewness(Wrapper):

    '''Manifestation of original Skewness object with skewness TimeSeries'''

    def __init__(self, skewness):
        self.skewness = skewness
        self.value = self.skewness

def WilliamPercentR(Wrapper):

    '''Manifestation of original WilliamPercentR object with william TimeSeries'''

    def __init__(self, william):
        self.william = william
        self.value = self.william

def IchimokuCloud(Wrapper):

    '''Manifestation of original IchimokuCloud object with ic TimeSeries'''

    pass # currently not implemented for the moment, not sure about the real form

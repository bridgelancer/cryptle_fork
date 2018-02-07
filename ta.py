# @Consider using recordclass API from MIT
class Candle:
    '''Mutable candle stick with namedtuple-like API.'''

    def __init__(self, o, c, h, l, t, v, nv):
        self._bar = [o, c, h, l, t, v, nv]

    def __getitem__(self, item):
        return self._bar[item]

    def __repr__(self):
        return self._bar.__repr__()

    @property
    def open(s):
        return s._bar[0]

    @property
    def close(s):
        return s._bar[1]

    @property
    def hi(s):
        return s._bar[2]

    @property
    def low(s):
        return s._bar[3]

    @property
    def volume(s):
        return s._bar[5]

    @property
    def nv(s):
        return s._bar[6]

    @open.setter
    def open(s, value):
        s._bar[0] = value

    @close.setter
    def close(s, value):
        s._bar[1] = value

    @hi.setter
    def hi(s, value):
        s._bar[2] = value

    @low.setter
    def low(s, value):
        s._bar[3] = value

    @volume.setter
    def volume(s, value):
        s._bar[5] = value

    @nv.setter
    def nv(s, value):
        s._bar[6] = value


class CandleBuffer:
    '''Container for candlesticks of a given length.

    Candle dependent metrics can be attached to a CandleBuffer instance. These
    metrics will then be pinged everytime a new candle is added to the buffer.
    Metrics must implement a ping() function which retrieves the newest candle
    from the buffer and update themselves accordingly.

    Args:
        period: Length of each candlestick of this collection
        maxcandles: Maximum number of historic candles to keep around

    Attributes:
        _bars: List of all the Candle objects
        _maxsize: Maximum number of historic candles to keep around
    '''

    def __init__(self, period, maxcandles=500):
        self._bars = []
        self._metrics = []
        self._period = period
        self._last_timestamp = None
        self._maxsize = maxcandles


    def pushTick(self, price, timestamp, volume=0, action=0):
        '''Provides public interface for accepting ticks'''
        # initialise the candle collection
        if self._last_timestamp is None:
            self._last_timestamp = timestamp
            self.pushInitCandle(price, timestamp, volume)

        # append previous n candles if no tick arrived in between
        elif self.barIndex(timestamp) != self.barIndex(self._last_timestamp):
            tmp_ts = self._last_timestamp + self.period
            while self.barIndex(tmp_ts) < self.barIndex(timestamp):
                self.pushEmptyCandle(self.last_close, tmp_ts)
                self._broadcast()
                tmp_ts += self.period

            self.pushInitCandle(price, timestamp, volume)
            self._broadcast()
            self._last_timestamp = timestamp

        # if tick arrived before next time period, update current candle
        elif self.barIndex(timestamp) == self.barIndex(self.last_timestamp):
            self.last_low = min(self.last_low , price)
            self.last_hi = max(self.last_hi, price)
            self.last_close = price
            self.last_volume += volume

        self.prune(self._maxsize)

    def pushCandle(self, o, c, h, l, t, v):
        '''Provides public interface for accepting aggregated candles'''
        self._bars.append(Candle(o, c, h, l, t, v))
        self._broadcast()


    def pushFullCandle(self, o, c, h, l, t, v):
        self._bars.append(Candle(o, c, h, l, t, v))
        self._broadcast()


    def pushInitCandle(self, price, timestamp, volume):
        self._bars.append(Candle(price, price, price, price, self.barIndex(timestamp), volume))
        return Candle(price, price, price, price, label, volume)


    def pushEmptyCandle(self, price, label):
        return Candle(price, price, price, price, label, 0)


    def attach(self, metric):
        self._metrics.append(metric)


    def barIndex(self, timestamp):
        return int(timestamp / self.period)


    def prune(self, size):
        try:
            self.bars = self.bars[-size:]
        except IndexError:
            raise ("Empty CandleBar cannot be pruned")

    def _broadcast(self):
        for metric in self.metrics:
            metric.ping()

    def __getitem__(self, item):
        return self.bars[item]

    def __len__(self):
        return len(self.bars)

    @property
    def last_open(s):
        return s.bars[-1].open

    @property
    def last_close(s):
        return s.bars[-1].close

    @property
    def last_hi(s):
        return s.bars[-1].hi

    @property
    def last_low(s):
        return s.bars[-1].low

    @property
    def last_volume(s):
        return s.bars[-1].volume

    @last_open.setter
    def last_open(s, value):
        s.bars[-1].open = value

    @last_close.setter
    def last_close(s, value):
        s.bars[-1].close = value

    @last_hi.setter
    def last_hi(s, value):
        s.bars[-1].hi = value

    @last_low.setter
    def last_low(s, value):
        s.bars[-1].low = value

    @last_volume.setter
    def last_volume(s, value):
        s.bars[-1].volume = value


class Metric:
    '''Base class with common functions of single valued metrics'''

    def __int__(self):
        return int(self._value)

    def __float__(self):
        return float(self._value)

    def __lt__(self, other):
        return self._value < other

    def __gt__(self, other):
        return self._value > other

    def __le__(self, other):
        return self._value <= other

    def __ge__(self, other):
        return self._value >= other

    def __repr__(self):
        return str(self._value)


class CandleMetric(Metric):
    '''Base class for candle dependent metrics'''

    def __init__(self, candle):
        self._candle = candle
        self._value = 0
        candle.attach(self)

    # @Rename
    # Give this function a better name, consider differentiating between pushing new candles and
    # pinging the metrics simply about new tick/close price
    def ping(self):
        raise NotImplementedError('Base class CandleMetric should not be called')


# The convention for new metrics is to use self._property for all internal attributes
# Ends with _new during deprecation period, these will replace the existing one soon
class SMA_new(CandleMetric):

    def __init__(self, candle, lookback):
        super().__init__(candle)
        self._lookback = lookback
        self._value = 0

    def ping(self):
        self._value = sum([x[0] for x in self._candle[-self._lookback :]]) / self._lookback


class WMA_new(CandleMetric):

    def __init__(self, candle, lookback, openp=True):
        super().__init__(candle)
        self._lookback = lookback
        self._value = 0
        self._weight = [x + 1 / (lookback * (lookback + 1) / 2) for x in range(lookback)]
        self._openp = openp

    def ping(self):
        prices = [x[0] if self._open_p else x[1] for x in self._candle[-self._lookback:]]
        self._value = sum(p * w for p,w in zip(prices, self._weight))


class EMA_new(CandleMetric):

    def __init__(self, candle, lookback, open_p=True):
        super().__init__(candle)
        self._lookback = lookback
        self._value = None
        self._weight = [x + 1 / (lookback * (lookback + 1) / 2) for x in range(lookback)]
        self._openp = openp

    def ping(self):
        if self._open_p:
            val = self._candle[-1][0]
        else:
            val = self._candle[-1][1]

        if self._value == None:
            self._value = val
            return

        self._value = self._weight * val + (1 - self._weight) * self._value


class RSI_new(CandleMetric):

    def __int__(self, candle, lookback):
        super().__init__(candle)
        self._lookback = lookback
        self._up = []
        self._down = []
        self._ema_up = None
        self._ema_down = None
        self._weight = 1 / lookback # MODIFIED to suit our purpose
        self._value = 0

    def ping(self):
        if len(self._candle) < 2:
            return

        if (self._candle[-1][0] > self._candle[-2][0]):
            self._up.append(abs(self._candle[-1][0] - self._candle[-2][0]))
            self._down.append(0)
        else:
            self._down.append(abs(self._candle[-2][0] - self._candle[-1][0]))
            self._up.append(0)

        if len(self._up) < self._lookback:
            return

        price_up = self._up[-1]
        price_down = self._down[-1]

        if self._ema_up == None and self._ema_down == None:
            # Initialization of ema_up and ema_down by simple averaging the up/down lists
            self._ema_up = sum([x for x in self._up]) / len(self._up)
            self._ema_down = sum([x for x in self._down]) / len(self._down)
        else:
            # Update ema_up and ema_down according to logistic updating formula
            self._ema_up = self._weight * price_up + (1 - self._weight) * self._ema_up
            self._ema_down = self._weight * price_down + (1 - self._weight) * self._ema_down

        # Handling edge cases and return the RSI index according to formula
        try:
            self._value = 100 - 100 / (1 +  self._ema_up/self._ema_down)
        except ZeroDivisionError:
            if self._ema_down == 0 and self._ema_up != 0:
                self._value = 100
            elif self._ema_up == 0 and self._ema_down != 0:
                self._value = 0
            elif self._ema_up == 0 and self._ema_down == 0:
                self._value = 50


class ATR_new:

    def __init__(self, candle, lookback):
        super().__init__(candle)
        self._lookback = lookback
        self._init = []
        self._value = 100000000

    def ping(self):
        if (len(self._init) < self._lookback + 1):
            self._init.append(self._candle[-1][2] - self._candle[-1][3]) # append bar max - bar min
            self._value = sum(self._init) / len(self._init)
        else:
            t1 = self._candle[-2][2] - self._candle[-2][3]
            t2 = abs(self._candle[-2][2] - self._candle[-3][1])
            t3 = abs(self._candle[-2][3] - self._candle[-3][1])
            tr = max(t1, t2, t3)
            self._value = (self._atr * (self._lookback - 1) + tr) / self._lookback


class CVWMA(Metric):

    def __init__(self, lookback):
        self._ticks = []
        self._lookback = lookback
        self._value = 0


    def pushTick(self, price, ts, volume, action):
        self._ticks.append((price, volume, ts, action))
        self.prune()

        try:
            assert timestamp >= self.ticks[0][2]
        except AssertionError:
            return
        except IndexError:
            pass

        self._volume += volume * action
        self._value += price * volume * action


    def prune(self):
        now = self.ticks[-1][2]
        epoch = now - self.period

        while True:
            if self.ticks[0][2] < epoch:
                tick = self.ticks.pop(0)
                price, volume, ts, action = tick

                self._volume -= volume * action
                self._value -= price * volume * action
            else:
                break


# @Deprecated
class ContinuousVWMA:

    def __init__(self, period):
        self.ticks = []
        self.volume = 0
        self.dollar_volume = 0

        self.period = period


    # Action: (1) is buy, (-1) is sell
    def update(self, price, timestamp, volume, action):

        self.ticks.append((price, volume, timestamp, action))
        self.prune()

        try:
            assert timestamp >= self.ticks[0][2]
        except AssertionError:
            return
        except IndexError:
            pass

        self.last = price

        self.volume += volume * action
        self.dollar_volume += price * volume * action


    def prune(self):
        now = self.ticks[-1][2]
        epoch = now - self.period

        while True:
            if self.ticks[0][2] < epoch:
                tick = self.ticks.pop(0)
                price, volume, ts, action = tick

                self.volume -= volume * action
                self.dollar_volume -= price * volume * action
            else:
                break

    @property
    def high(self):
        return max(self.ticks)

    @property
    def low(self):
        return min(self.ticks)

    def __int__(self):
        return self.dollar_volume

    def __float__(self):
        return self.dollar_volume

    def __lt__(self, other):
        return self.dollar_volume < other

    def __gt__(self, other):
        return self.dollar_volume > other

    def __repr__(self):
        return str(self.dollar_volume)


# @Deprecated
class CandleBar:

    # bars: List of (open, close, high, low, nth minute bar)
    # This class is for storing the min-by-min bars the minute before the current tick
    def __init__(self, period):
        self.bars = []
        self.metrics = []
        self.period = period
        self.last_timestamp = None
        self.last = 0

    def __getitem__(self, item):
        return self.bars[item]

    def __len__(self):
        return len(self.bars)

    def update(self, price, timestamp, volume, action=0):

        if self.last_timestamp == None:
            self.volume = volume
            self.last_timestamp = timestamp
            self.net_volume = volume * action

            self.bars.append(Candle(price, price, price, price, int(timestamp/self.period), volume, volume * action))

            for metric in self.metrics:
                metric.update()

        # append previous n candle bars if no tick arrives between the n candles
        elif int(timestamp / self.period) != int(self.last_timestamp / self.period):
            timestamp_tmp = self.last_timestamp + self.period

            # append the in between bars if the next tick arrives 1+ bar after the previous one, if there is any
            while int(timestamp_tmp / self.period) < int(timestamp / self.period):
                self.bars.append(Candle(self.last_close, self.last_close, self.last_close,
                    self.last_close, int(timestamp_tmp/self.period), 0, 0))

                for metric in self.metrics:
                    metric.update()

                timestamp_tmp = timestamp_tmp + self.period

            # append the new bar that contains the newly arrived tick
            self.bars.append(Candle(price, price, price, price, int(timestamp/self.period), volume,self.net_volume))

            for metric in self.metrics:
                metric.update()

            self.last_timestamp = timestamp
            print("Start of bar volume: "+ str(self.last_volume))
            print("Start of bar Net volume: "+ str(self.last_nv))


        elif int(timestamp / self.period) == int(self.last_timestamp / self.period):
            self.last_low = min(self.last_low , price)
            self.last_hi = max(self.last_hi, price)
            self.last_close = price
            self.last_volume += volume
            self.last_nv += volume * action
            print("Interbar volume: "+ str(self.last_volume))
            print("Intrabar Net volume: "+ str(self.last_nv))

        self.last = price

    def prune(self, size):
        try:
            self.bars = self.bars[-size:]
        except IndexError:
            raise ("Empty CandleBar cannot be pruned!")

    @property
    def last_open(s):
        return s.bars[-1].open

    @property
    def last_close(s):
        return s.bars[-1].close

    @property
    def last_hi(s):
        return s.bars[-1].hi

    @property
    def last_low(s):
        return s.bars[-1].low

    @property
    def last_volume(s):
        return s.bars[-1].volume

    @property
    def last_nv(s):
        return s.bars[-1].nv

    @last_open.setter
    def last_open(s, value):
        s.bars[-1].open = value

    @last_close.setter
    def last_close(s, value):
        s.bars[-1].close = value

    @last_hi.setter
    def last_hi(s, value):
        s.bars[-1].hi = value

    @last_low.setter
    def last_low(s, value):
        s.bars[-1].low = value

    @last_volume.setter
    def last_volume(s, value):
        s.bars[-1].volume = value

    @last_nv.setter
    def last_nv(s, value):
        s.bars[-1].nv = value


# @Deprecated
class RSI():

    def __init__(self, candle, lookback):
        self.candle = candle
        self.lookback = lookback
        self.up = []
        self.down = []
        self.ema_up = None
        self.ema_down = None
        self.weight = 1 / lookback # MODIFIED to suit our purpose
        self.rsi = 0

        candle.metrics.append(self)


    def update(self):

        if len(self.candle.bars) < 2:
            return
        else:
            pass

        if (self.candle[-1][0] > self.candle[-2][0]):
            self.up.append(abs(self.candle[-1][0] - self.candle[-2][0]))
            self.down.append(0)
        else:
            self.down.append(abs(self.candle[-2][0] - self.candle[-1][0]))
            self.up.append(0)

        if len(self.up) < self.lookback:
            return
        else:
            pass

        price_up = self.up[-1]
        price_down = self.down[-1]

        # Initialization of ema_up and ema_down by simple averaging the up/down lists
        if self.ema_up == None and self.ema_down == None:
            self.ema_up = sum([x for x in self.up]) / len(self.up)
            self.ema_down = sum([x for x in self.down]) / len(self.down)

            try:
                self.rsi = 100 - 100 / (1 +  self.ema_up/self.ema_down)
            except ZeroDivisionError:
                if self.ema_down == 0 and self.ema_up != 0:
                    self.rsi = 100
                elif self.ema_up == 0 and self.ema_down != 0:
                    self.rsi = 0
                elif self.ema_up == 0 and self.ema_down == 0:
                    self.rsi = 50
            return
        else:
            pass

        # Update ema_up and ema_down according to logistic updating formula
        self.ema_up = self.weight * price_up + (1 - self.weight) * self.ema_up
        self.ema_down = self.weight * price_down + (1 - self.weight) * self.ema_down

        # Handling edge cases and return the RSI index according to formula
        try:
            self.rsi = 100 - 100 / (1 +  self.ema_up/self.ema_down)
        except ZeroDivisionError:
            if self.ema_down == 0 and self.ema_up != 0:
                self.rsi = 100
            elif self.ema_up == 0 and self.ema_down != 0:
                self.rsi = 0
            elif self.ema_up == 0 and self.ema_down == 0:
                self.rsi = 50

    def __float__(self):
        return self.rsi

    def __lt__(self, other):
        return self.rsi < other

    def __gt__(self, other):
        return self.rsi > other

    def __le__(self, other):
        return self.rsi <= other

    def __ge__(self, other):
        return self.rsi >= other

    def __repr__(self):
        return str(self.rsi)


# @Deprecated
class ATR():

    def __init__(self, candle, lookback):
        self.candle = candle
        self.lookback = lookback
        self.init = []
        self.atr = 10000000

        candle.metrics.append(self)


    def update(self):
        if (len(self.init) < self.lookback + 1):
            self.init.append(self.candle[-1][2] - self.candle[-1][3]) # append bar max - bar min
            self.atr = sum(self.init) / len(self.init)
        else:
            t1 = self.candle[-2][2] - self.candle[-2][3]
            t2 = abs(self.candle[-2][2] - self.candle[-3][1])
            t3 = abs(self.candle[-2][3] - self.candle[-3][1])
            tr = max(t1, t2, t3)
            self.atr = (self.atr * (self.lookback - 1) + tr) / self.lookback

    def __float__(self):
        return self.atr

    def __lt__(self, other):
        return self.atr < other

    def __gt__(self, other):
        return self.atr > other

    def __le__(self, other):
        return self.atr <= other

    def __ge__(self, other):
        return self.atr >= other

    def __repr__(self):
        return str(self.atr)


# @Deprecated
class SMA():

    def __init__(self, candle, lookback):
        self.candle = candle
        self.lookback = lookback
        self.sma = 0

        candle.metrics.append(self)


    def update(self):
        self.sma = (sum([x[0] for x in self.candle[-self.lookback :]])) / self.lookback


    def __repr__(self):
        return str(self.wma)


# @Deprecated
class WMA():

    def __init__(self, candle, lookback):
        self.candle = candle
        self.lookback = lookback
        self.wma = 0
        self.weight = [x / (lookback * (lookback + 1) / 2) for x in range(1, lookback + 1)]

        candle.metrics.append(self)


    def update(self, open_p = True):

        if len(self.candle) < (self.lookback - 1):
            pass

        else:
            price_list = []
            bar_list = self.candle[-self.lookback:]

            if open_p == True:
                price_list = [x[0] for x in bar_list]
            elif open_p == False:
                price_list = [x[1] for x in bar_list] # this is currently not correct

            self.price_list_test = price_list
            self.wma = sum(p * w for p,w in zip(price_list, self.weight))


    def __repr__(self):
        return str(self.wma)


# @Deprecated
class EMA():

    def __init__(self, candle, lookback):

        self.candle = candle
        self.lookback = lookback
        self.ema = None
        self.weight =  2 / (lookback + 1)

        candle.metrics.append(self)


    def update(self, open_p=True):

        if open_p:
            val = self.candle[-1][0]
        else:
            val = self.candle[-1][1] # the [-1] is the current bar close (i.e. changing, not intended)

        if self.ema == None:
            self.ema = val
            return

        self.ema = self.weight*val + (1-self.weight)*self.ema


    def __repr__(self):
        return str(self.wma)

class EMA_NetVol():

    def __init__(self, candle, lookback):

        self.candle = candle
        self.lookback = lookback
        self.ema = None
        self.weight =  1 / lookback

        candle.metrics.append(self)


    def update(self):
        if len(self.candle) < 2:
            return

        val = self.candle[-2][6]
        print("Last net vol:" + str(val))
        if self.ema == None:
            self.ema = val
            return

        self.ema = self.weight*val + (1-self.weight)*self.ema


    def __repr__(self):
        return str(self.wma)

# @Deprecated - this is an ad hoc instance for quick deployment, not intended to be used in the future
class BNB():
    # This class takes the band value of a BollingerBand object and apply a bollinger band on it (BNB)
    def __init__(self, bollinger, lookback):

        self.bollinger = bollinger # Take a BollingerBand object
        self.lookback = lookback
        self.sma = []
        self.width = 0
        self.upperband = 0
        self.lowerband = 0
        self.band = 0
        self.ls = []

        bollinger.sma.candle.metrics.append(self)


    def update(self, open_p=True):
        ls = self.ls


        if len(ls) < self.lookback:
            lookback = len(ls)
            ls.append(0)
        else:
            lookback = self.lookback
            ls.append(self.bollinger.band)

        if len(self.sma) < self.lookback + self.bollinger.lookback:
            self.sma.append(0)
        else:
            self.sma.append(sum([x for x in ls[-lookback:]]) / self.lookback)

        sma_ls = [x for x in self.sma[-lookback:]]
        ls = [x for x in self.ls[-lookback:]]

        try:
            mean = sum(ls) / lookback
            mean_square = list(map(lambda y: (y - mean) ** 2, ls))

            self.width = ( sum(mean_square) / lookback ) ** 0.5

            self.upperband = self.sma[-1] + 0.5* self.width
            self.lowerband = self.sma[-1] - 0.5* self.width
            if all(item != 0 for item in sma_ls):
                self.band = ( self.upperband / self.lowerband - 1 ) * 100
            else:
                self.band = 0
        except ZeroDivisionError:
            self.band = 0

    def __repr__(self):
        return str(self.wma)


# @Deprecated
class MACD_WMA():

    # wma1 and wma2 needs to use the same candle instance
    def __init__(self, wma1, wma2, lookback):

        self.wma1 = wma1
        self.wma2 = wma2
        self.wma3 = None
        self.macd = None
        self.lookback = lookback
        self.past = []
        self.weight = [x / (lookback * (lookback + 1) / 2) for x in range(1, lookback + 1)]

        wma1.candle.metrics.append(self)

    def update(self):

        macd = self.wma1.wma - self.wma2.wma
        # append the diff of wma to the list past
        self.past.append(macd)

        # @TODO past should only store lookback # of differenced wma

        if len(self.past) < (self.lookback - 1):
            pass

        else:
            price_list = []
            price_list = self.past[-self.lookback:]

            self.price_list_test = price_list
            self.wma3 = sum(p * w for p,w in zip(price_list, self.weight))

        self.macd = macd
        self.diff = self.macd
        self.diff_ma = self.wma3


# @Deprecated
class MACD():

    # ema1 and ema2 needs to use the same candle instance
    def __init__(self, ema1, ema2, lookback):

        self.ema1 = ema1
        self.ema2 = ema2
        self.macd = 0
        self.ema3 = None
        self.diff = None
        self.lookback = lookback
        self.past = []
        self.weight = 2 / (lookback + 1)

        ema1.candle.metrics.append(self)

    def update(self):

        self.macd = self.ema1.ema - self.ema2.ema
        self.past.append(self.macd)

        val = self.past[-1]

        if self.ema3 == None:
            self.ema3 = val
            return

        self.ema3 = self.weight*val + (1-self.weight)*self.ema3

        self.diff = self.macd
        self.diff_ma = self.ema3


# @Deprecated
class BollingerBand():

    def __init__(self, sma, lookback):

        self.sma = sma
        self.lookback = lookback
        self.width = 0
        self.upperband = 0
        self.lowerband = 0
        self.band = 0

        sma.candle.metrics.append(self)

    # the default width is defined by +/- 2 sd
    def update(self):
        sma = self.sma
        if len(sma.candle) < self.lookback:
            lookback = len(sma.candle)
        else:
            lookback = self.lookback

        ls = [x[0] for x in sma.candle[-lookback:]]
        self.ls = ls

        mean = sum(ls) / lookback
        mean_square = list(map(lambda y: (y - mean) ** 2, ls))

        self.width = ( sum(mean_square) / lookback ) ** 0.5

        self.upperband = self.sma.candle.bars[-1][1] + 2 * self.width
        self.lowerband = self.sma.candle.bars[-1][1] - 2 * self.width
        self.band = ( self.upperband / self.lowerband - 1 ) * 100

    def __float__(self):
        return self.band

    def __lt__(self, other):
        return self.band < other

    def __gt__(self, other):
        return self.band > other

    def __le__(self, other):
        return self.band <= other

    def __ge__(self, other):
        return self.band >= other

    def __repr__(self):
        return str({'band': self.band, 'upperband': self.upperband, 'lowerband': self.lowerband})

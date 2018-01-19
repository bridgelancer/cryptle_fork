class ContinuousVWMA:

    def __init__(self, period):
        self.ticks = []
        self.volume = 0
        self.dollar_volume = 0

        self.period = period


    # Action: (1) is buy, (-1) is sell
    def update(self, price, volume, timestamp, action):

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

    def high(self):
        return max(self.ticks)


    def low(self):
        return min(self.ticks)



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


    def update(self, price, timestamp, volume=0):

        if self.last_timestamp == None:
            self.barmin = self.barmax = self.baropen = self.barclose = price
            self.volume = volume
            self.last_timestamp = timestamp

        elif int(timestamp / self.period) != int(self.last_timestamp / self.period):
            self.bars.append(
                (
                    self.baropen,
                    self.barclose,
                    self.barmax,
                    self.barmin,
                    int(timestamp/self.period),
                    self.volume
                )
            )

            self.barmin = self.barmax = self.baropen = self.barclose = price
            self.volume = volume
            self.last_timestamp = timestamp

            # Update all attached candle chart dependent metrics
            for metric in self.metrics:
                metric.update()

        elif int(timestamp / self.period) == int(self.last_timestamp / self.period):
            self.barmin = min(self.barmin, price)
            self.barmax = max(self.barmax, price)
            self.barclose = price
            self.volume += volume

        self.last = price


    def prune(self, size):
        try:
            self.bars = self.bars[-size:]
        except IndexError:
            raise ("Empty CandleBar cannot be pruned!")



class ATR():

    def __init__(self, candle, lookback):
        self.candle = candle
        self.lookback = lookback
        self.init = []
        self.atr = 10000000

        candle.metrics.append(self)


    def update(self):
        if (len(self.init) < self.lookback):
            self.init.append(self.candle[-1][2] - self.candle[-1][3]) # append bar max - bar min
            self.atr = sum(self.init) / len(self.init)
        else:
            t1 = self.candle[-1][2] - self.candle[-1][3]
            t2 = abs(self.candle[-1][2] - self.candle[-2][1])
            t3 = abs(self.candle[-1][3] - self.candle[-2][1])
            tr = max(t1, t2, t3)
            self.atr = (self.atr * (self.lookback - 1) + tr) / self.lookback



class SMA():

    def __init__(self, candle, lookback):
        self.candle = candle
        self.lookback = lookback
        self.sma = 0

        candle.metrics.append(self)


    def update(self):
        self.sma = sum([x[0] for x in self.candle[-self.lookback:]]) / self.lookback



class WMA():

    def __init__(self, candle, lookback):
        self.candle = candle
        self.lookback = lookback
        self.wma= 0
        self.weight = [x / (lookback * (lookback + 1) / 2) for x in range(1, lookback + 1)]

        candle.metrics.append(self)


    def update(self, open_p = True):

        if len(self.candle) < (self.lookback-1):
            pass

        else:
            price_list = []
            bar_list = self.candle[-(self.lookback- 1):]

            if open_p == True:
                price_list = [x[0] for x in bar_list]
                price_list.append(self.candle.baropen)
            elif open_p == False:
                price_list = [x[1] for x in bar_list]
                price_list.append(self.candle.barclose)

            self.price_list_test = price_list
            self.wma = sum(p * w for p,w in zip(price_list, self.weight))



class EMA():

    def __init__(self, candle, lookback):

        self.candle = candle
        self.lookback = lookback
        self.ema = None
        self.weight =  2 / (lookback + 1)

        candle.metrics.append(self)


    def update(self, open_p=True):

        if open_p:
            price = self.candle[-1][0]
        else:
            price = self.candle[-1][1]

        if self.ema == None:
            self.ema = price
            return

        self.ema = self.weight*price + (1-self.weight)*self.ema



class MACD():

    # ema1 and ema2 needs to use the same candle instance
    def __init__(self, ema1, ema2, lookback):

        self.ema1 = ema1
        self.ema2 = ema2
        self.macd = 0
        self.ema3 = None
        self.lookback = lookback
        self.past = []
        self.weight = 2 / (lookback + 1)

        ema1.candle.metrics.append(self)

    def update(self):

        self.macd = self.ema1.ema - self.ema2.ema
        self.past.append(self.macd)

        price = self.past[-1]

        if self.ema3 == None:
            self.ema3 = price
            return

        self.ema3 = self.weight*price + (1-self.weight)*self.ema3



class BollingerBand():

    def __init__(self, sma, lookback):

        self.sma = sma
        self.lookback = lookback
        self.width = 0
        self.upperband = 0
        self.lowerband = 0

        sma.candle.metrics.append(self)

    def update(self):
        mean_squared = 0
        sma = self.sma
        lookback = self.lookback

        ls = [x[0] for x in sma.candle[-lookback:]]
        mean = sum(ls) / lookback
        mean_square = list(map(lambda y: (y - mean) ** 2, ls))

        self.width = (sum(mean_square) / lookback) ** 0.5
        self.upperband = sma.candle[-1][0] + 2 * self.width
        self.lowerband = sma.candle[-1][0] - 2 * self.width
        self.band = (self.upperband/self.lowerband - 1) * 100


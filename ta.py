class ContinuousVWMA:

    # window is the number of seconds in the lookback window
    # Ticker (optional) is meta-info about what series is being tracked
    def __init__(self, lookback):
        self.ticks = []
        self.avg = 0
        self.volume = 0
        self.dollar_volume = 0

        self.lookback = lookback


    def update(self, price, volume, timestamp):

        # @THROW @HANDLE
        try:
            assert timestamp > self.ticks[0][2]
        except AssertionError:
            return
        except IndexError:
            pass

        self.last = price

        self.volume += volume
        self.dollar_volume += price * volume
        self.avg = self.dollar_volume / self.volume

        self.ticks.append((price, volume, timestamp))
        self.prune()


    def prune(self):
        now = self.ticks[-1][2]
        epoch = now - self.lookback

        while True:
            if self.ticks[0][2] <= epoch:
                tick = self.ticks.pop(0)

                self.volume -= tick[1]
                self.dollar_volume -= tick[0] * tick[1]
                self.avg = self.dollar_volume / self.volume
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

        self.lookback = 100
        self.last = 0

    def __getitem__(self, item):
        return self.bars[item]


    def update(self, price, timestamp):

        if self.last_timestamp == None:
            self.barmin = self.barmax = self.baropen = self.barclose = price
            self.last_timestamp = timestamp

        elif int(timestamp / self.period) != int(self.last_timestamp / self.period):
            self.bars.append([self.baropen, self.barclose, self.barmax, self.barmin, int(timestamp/self.period)])

            self.barmin = self.barmax = self.baropen = self.barclose = price
            self.last_timestamp = timestamp

            for metric in metrics:
                metric.update()

        elif int(timestamp / self.period) == int(self.last_timestamp / self.period):
            self.barmin = min(self.barmin, price)
            self.barmax = max(self.barmax, price)
            self.barclose = price

        self.last = price


    def prune(self, size):
        try:
            self.bars = self.bars[-size:]
        except IndexError:
            raise ("Empty CandleBar cannot be pruned!")


    def computeWMA(self,open_p = True):

        if len(self.bars) < (self.scope-1):
            pass

        else:
            price_list = []
            bar_list = self.bars[-(self.scope - 1):]

            if open_p == True:
                price_list = [x[0] for x in bar_list]
                price_list.append(self.baropen)
            elif open_p == False:
                price_list = [x[1] for x in bar_list]
                price_list.append(self.barclose)

            sequence = range(1,(self.scope + 1))
            self.price_list_test = price_list
            weight = list(map(lambda x: x/sum(sequence), sequence))
            self.WMA = sum(p * w for p,w in zip(price_list, weight))
            self.WMAs.append(self.WMA)



class ATR():

    def __init__(self, candle, lookback):
        self.candle = candle
        self.lookback = lookback
        self.init = []
        self.atr = 0

        candle.metrics.append(self)

    def update(self):
        if (len(self.init) < self.lookback):
            self.init.append(self.bars[-1][2] - self.bars[-1][3])
            self.atr = sum(self.init) / len(self.init)
        else:
            t1 = self.candle[-1][2] - self.candle[-1][3]
            t2 = abs(self.candle[-1][2] - self.candle[-2][1])
            t3 = abs(self.candle[-1][3] - self.candle[-2][1])
            tr = max(t1, t2, t3)
            self.atr = (self.atr * (self.lookback - 1) + tr) / self.lookback



class SMA():

    def __init__(self, candle, lookback):



class WMA():

    def __init__(self, candle, lookback):



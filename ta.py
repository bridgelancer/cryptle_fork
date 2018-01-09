import time


class MovingWindow:

    # window is the number of seconds in the lookback window
    # Ticker (optional) is meta-info about what series is being tracked
    def __init__(self, window):
        self._ticks = []

        self.avg = 0
        self.volume = 0
        self.dollar_volume = 0

        self.window = window


    def update(self, price, volume, timestamp):
        self.last = price
        self.volume = self.volume + volume
        self.dollar_volume = self.dollar_volume + price * volume
        self.avg = self.dollar_volume / self.volume

        self._ticks.append((price, volume, timestamp))
        self.clear()


    def clear(self):
        now = time.time()
        lookback = now - self.window

        while True:
            if self._ticks[0][2] < lookback:
                tick = self._ticks.pop(0)
                self.volume = self.volume - tick[1]
                self.dollar_volume = self.dollar_volume - tick[0] * tick[1]
                self.avg = self.dollar_volume / self.volume
            else:
                break


    def high(self):
        return max(self._ticks)


    def low(self):
        return min(self._ticks)



class CandleBar:

    # _bars: List of (open, close, high, low, nth minute bar)
    # This class is for storing the min-by-min bars the minute before the current tick
    # default bar size is 1 minute
    def __init__(self, period=60, atr_lookback=5):
        self._bars = []

        self.period = period
        self.lookback = 100
        self.last = 0

        self.ls = []
        self.atr_val = 0
        self.atr_lookback = atr_lookback

        self.barmin = None
        self.barmax = None
        self.baropen = None
        self.barclose = None
        self.timestamp_last = None


    def update(self, price, timestamp):

        if timestamp == None:
            timestamp = time.time()

        if self.timestamp_last == None:
            self.barmin = self.barmax = self.baropen = self.barclose = price
            self.timestamp_last = timestamp

        elif int(timestamp / self.period) != int(self.timestamp_last / self.period):
            self._bars.append([self.baropen, self.barclose, self.barmax, self.barmin, int(timestamp/self.period) + 1])

            self.barmin = self.barmax = self.baropen = self.barclose = price
            self.timestamp_last = timestamp
            self.computeAtr()

        elif int(timestamp / self.period) == int(self.timestamp_last / self.period):
            self.barmin = min(self.barmin, price)
            self.barmax = max(self.barmax, price)
            self.barclose = price

        self.last = price  # update the current tick prcie
        self.prune(self.lookback)


    def computeAtr(self):
        if (len(self._bars) <= self.atr_lookback and len(self._bars) > 0):
            self.ls.append(self._bars[-1][2] - self._bars[-1][3])
            self.atr_val = sum(self.ls) / len(self.ls)
        elif(len(self._bars) > mins):
            self.ls.clear()
            TR = self._bars[-1][2] - self._bars[-1][3]
            self.atr_val = (self.atr_val * (self.atr_lookback- 1) + TR) / self.atr_lookback


    def getAtr(self):

        if (len(self._bars) >= self.atr_lookback):
            return self.atr_val
        else:
            raise RuntimeWarning("ATR not yet available")


    def prune(self, lookback): #discard the inital bars after 100 periods of bar data
        if len(self._bars) != 0:
            self._bars = self._bars[-min(len(self._bars), lookback):]


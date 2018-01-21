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

        # append previous n candle bars if no tick arrives between the n candles
        # the first bar to be appended
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
            # Update all attached candle dependent metrics for the bar of last tick
            if (int(timestamp / self.period) == int(self.last_timestamp / self.period) + 1):
                for metric in self.metrics:
                    metric.update(price)
            else:
                for metric in self.metrics:
                    metric.update(self.barclose)

            timestamp_tmp = self.last_timestamp + self.period
            # append the in between bars if the next tick arrives 1+ bar after the previous one
            while int(timestamp_tmp / self.period) < int(timestamp / self.period):
                self.bars.append(
                    (
                        self.barclose,
                        self.barclose,
                        self.barclose,
                        self.barclose,
                        int(timestamp_tmp/self.period),
                        0
                    )
                )
                # Update all attached candle dependent metrics for the subsequent empty bars, if any
                if (int(timestamp_tmp / self.period) == int(timestamp / self.period) - 1):
                    for metric in self.metrics:
                        metric.update(price)
                else:
                    for metric in self.metrics:
                        metric.update(self.barclose)
                timestamp_tmp = timestamp_tmp + self.period

            self.barmin = self.barmax = self.baropen = self.barclose = price
            self.volume = volume
            self.last_timestamp = timestamp


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


class RSI():

    def __init__(self, candle, lookback):
        self.candle = candle
        self.lookback = lookback
        self.up = []
        self.down = []
        self.ema_up = None
        self.ema_down = None
        self.weight = 2/ (lookback + 1)
        self.rsi = 0

        candle.metrics.append(self)


    def update(self):

        if (self.candle.baropen > self.candle[-1][0]):
            self.up.append(self.candle.baropen - self.candle[-1][0])
            self.down.append(0)
        else:
            self.down.append(self.candle[-1][0] - self.candle.baropen)
            self.up.append(0)

        if len(self.up) < self.lookback:
            return
        else:
            pass

        price_up = self.up[-1]
        price_down = self.down[-1]

        if self.ema_up == None and self.ema_down == None:
            self.ema_up = price_up
            self.ema_down = price_down
            return
        else:
            pass

        self.ema_up = self.weight*price_up + (1 - self.weight)*self.ema_up
        self.ema_down = self.weight*price_down + (1-self.weight)*self.ema_down

        self.rsi = 100 - 100 / (1 +  self.ema_up/self.ema_down)




class ATR():

    def __init__(self, candle, lookback):
        self.candle = candle
        self.lookback = lookback
        self.init = []
        self.atr = 10000000

        candle.metrics.append(self)


    def update(self, price):
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


    def update(self, price):
        self.sma = (price + sum([x[0] for x in self.candle[-(self.lookback - 1):]])) / self.lookback



class WMA():

    def __init__(self, candle, lookback):
        self.candle = candle
        self.lookback = lookback
        self.wma= 0
        self.weight = [x / (lookback * (lookback + 1) / 2) for x in range(1, lookback + 1)]

        candle.metrics.append(self)


    def update(self, price, open_p = True):

        if len(self.candle) < (self.lookback-1):
            pass

        else:
            price_list = []
            bar_list = self.candle[-(self.lookback- 1):]

            if open_p == True:
                price_list = [x[0] for x in bar_list]
                price_list.append(price)
            elif open_p == False:
                price_list = [x[1] for x in bar_list]
                price_list.append(price)

            print (price_list)
            self.price_list_test = price_list
            self.wma = sum(p * w for p,w in zip(price_list, self.weight))



class EMA():

    def __init__(self, candle, lookback):

        self.candle = candle
        self.lookback = lookback
        self.ema = None
        self.weight =  2 / (lookback + 1)

        candle.metrics.append(self)


    def update(self, price, open_p=True):

        if open_p:
            val = price
        else:
            val = self.candle[-1][1] # last close should be valid

        if self.ema == None:
            self.ema = val
            return

        self.ema = self.weight*val + (1-self.weight)*self.ema



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

        val = self.past[-1]

        if self.ema3 == None:
            self.ema3 = val
            return

        self.ema3 = self.weight*val + (1-self.weight)*self.ema3



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
    def update(self, price):
        sma = self.sma
        lookback = self.lookback

        ls = [x[0] for x in sma.candle[-(lookback - 1):]]
        ls = ls + [price]

        mean = sum(ls) / lookback
        mean_square = list(map(lambda y: (y - mean) ** 2, ls))

        self.width = ( sum(mean_square) / lookback ) ** 0.5

        self.upperband = price + 2 * self.width
        self.lowerband = price - 2 * self.width
        self.band = ( self.upperband / self.lowerband - 1 ) * 100


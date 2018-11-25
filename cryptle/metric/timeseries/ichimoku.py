from metric.base import Timeseries

# not functional, fix only if necessary
class IchimokuCloud(Timeseries):
    def __init__(self, ts, short, long, base):
        self._ts    = ts
        self._short = short
        self._long  = long
        self._base  = base
        self.value  = 0
        self._cache = []

    @Timeseries.cache
    def evaluate(self):
        window = self._cache[-max(self._short, self._long, self._base)-1:-1]
        # pending confirmation, refer to williamR.py
        high_prices = [x.high for x in window]
        low_prices  = [x.low  for x in window]

        tenkan_sen = (max(high_prices[-self._short:]) + min(low_prices[-self._short:])) / 2
        kijun_sen  = (max(high_prices[-self._long:])  + min(low_prices[-self._long:])) / 2
        A = (tenkan_sen + kijun_sen) / 2
        B = (max(high_prices[-self._base:]) + min(low_prices[-self._base:])) / 2

    def onTick(self, price, timestamp, volume, action):
        raise NotImplementedError


from cryptle.metric.base import Timeseries
from cryptle.event import on, Bus

''' Temporary solution for passing timestamp to various Timeseries object '''


class Timestamp(Timeseries):
    def __init__(self, lookback):
        super().__init__()
        self._lookback = lookback
        self._ts = []
        self.value = None
        self.name = 'Timestamp'

    @on('aggregator:new_timestamp')
    def appendTS(self, timestamp):
        self._ts.append(timestamp)
        self.evaluate()
        self.broadcast()
        self.prune()

    def evaluate(self):
        try:
            self.value = float(self._ts[-1])
        except:
            self.value = None

    def prune(self):
        pass

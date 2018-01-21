import logging

# CRITICAL = 50
# ERROR    = 40
# WARNING  = 30
# INFO     = 20
# DEBUG    = 10
# NOTSET   = 0

logging.SIGNAL  = 27
logging.REPORT  = 25
logging.INDEX   = 7
logging.TICK    = 5

logging.addLevelName(logging.SIGNAL, 'SIGNAL')
logging.addLevelName(logging.REPORT, 'REPORT')
logging.addLevelName(logging.INDEX, 'INDEX')
logging.addLevelName(logging.TICK, 'TICK')


def signal(self, message, *args, **kargs):
    if self.isEnabledFor(logging.SIGNAL):
        self._log(logging.SIGNAL, message, args, **kws)

def report(self, message, *args, **kws):
    if self.isEnabledFor(logging.REPORT):
        self._log(logging.REPORT, message, args, **kws)

def index(self, message, *args, **kargs):
    if self.isEnabledFor(logging.INDEX):
        self._log(logging.INDEX, message, args, **kws)

def tick(self, message, *args, **kargs):
    if self.isEnabledFor(logging.TICK):
        self._log(logging.TICK, message, args, **kws)

logging.Logger.signal = signal
logging.Logger.report = report
logging.Logger.index  = index
logging.Logger.tick   = tick


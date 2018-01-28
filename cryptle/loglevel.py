import logging

# CRITICAL = 50
# ERROR    = 40
# WARNING  = 30
# INFO     = 20
# DEBUG    = 10
# NOTSET   = 0

# Define new log levels
logging.REPORT  = 25
logging.SIGNAL  = 23
logging.INDEX   = 7
logging.TICK    = 5

logging.addLevelName(logging.REPORT, 'REPORT')
logging.addLevelName(logging.SIGNAL, 'SIGNAL')
logging.addLevelName(logging.INDEX, 'INDEX')
logging.addLevelName(logging.TICK, 'TICK')


# Add convenience functions to the default Logger and it's children instances
def _report(self, message, *args, **kargs):
    if self.isEnabledFor(logging.REPORT):
        self._log(logging.REPORT, message, args, **kargs)

def _signal(self, message, *args, **kargs):
    if self.isEnabledFor(logging.SIGNAL):
        self._log(logging.SIGNAL, message, args, **kargs)

def _index(self, message, *args, **kargs):
    if self.isEnabledFor(logging.INDEX):
        self._log(logging.INDEX, message, args, **kargs)

def _tick(self, message, *args, **kargs):
    if self.isEnabledFor(logging.TICK):
        self._log(logging.TICK, message, args, **kargs)

logging.Logger.report = _report
logging.Logger.signal = _signal
logging.Logger.index  = _index
logging.Logger.tick   = _tick


# Define a unified formatter for cross module use
def defaultFormatter(notimestamp=False):

    if notimestamp:
        fmt = '%(name)-10s [%(levelname)-8s] %(message)s'
    else:
        fmt = '%(name)-10s: %(asctime)s [%(levelname)-8s] %(message)s'

    datefmt = '%Y-%m-%d %H:%M:%S'
    return logging.Formatter(fmt=fmt, datefmt=datefmt)


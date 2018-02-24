'''
Defines custom log levels, as well as provides logging helper functions.
'''
import logging


logging.REPORT  = 25
logging.SIGNAL  = 15
logging.METRIC  = 13
logging.TICK    = 5
logging.addLevelName(logging.REPORT, 'REPORT')
logging.addLevelName(logging.SIGNAL, 'SIGNAL')
logging.addLevelName(logging.METRIC, 'METRIC')
logging.addLevelName(logging.TICK, 'TICK')


# Add named log functions to Logger base class
def _report(self, message, *args, **kargs):
    if self.isEnabledFor(logging.REPORT):
        self._log(logging.REPORT, message, args, **kargs)

def _signal(self, message, *args, **kargs):
    if self.isEnabledFor(logging.SIGNAL):
        self._log(logging.SIGNAL, message, args, **kargs)

def _metric(self, message, *args, **kargs):
    if self.isEnabledFor(logging.METRIC):
        self._log(logging.METRIC, message, args, **kargs)

def _tick(self, message, *args, **kargs):
    if self.isEnabledFor(logging.TICK):
        self._log(logging.TICK, message, args, **kargs)

logging.Logger.report = _report
logging.Logger.signal = _signal
logging.Logger.metric = _metric
logging.Logger.tick   = _tick


# Standardised formatter
def std_formatter(notimestamp=False):
    if notimestamp:
        fmt = '%(name)-10s [%(levelname)-8s] %(message)s'
    else:
        fmt = '%(name)-10s: %(asctime)s [%(levelname)-8s] %(message)s'

    datefmt = '%Y-%m-%d %H:%M:%S'
    return logging.Formatter(fmt=fmt, datefmt=datefmt)


def std_logger(name, *file_handlers, loglevel=logging.DEBUG):
    logger = logging.getLogger(name)
    logger.setLevel(loglevel)
    for fh in file_handlers:
        logger.addHandler(fh)
    return logger


def std_filehandler(fname, loglevel=logging.DEBUG, formatter=std_formatter()):
    fh = logger.FileHandler(fname)
    fh.setLevel(loglevel)
    fh.setFormatter(formatter)
    return fh

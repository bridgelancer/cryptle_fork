"""
This module defines custom log levels, and provide logging related helpers.

The custom log levels are trading related events. They are all defined with
severity below WARNING, described as follows:
- REPORT  25
- SIGNAL  15
- METRIC  13
- TICK    5

When imported to other modules, loggers created from logging.getLogger will have
a log method for each corresponding new log level.

Helper functions create handled loggers or loggers and handlers in pairs.

Default formatters subclassed from logging.Formatter provide a unified log
format for Cryptle. Indivial modules are recommended to use the formatters
defined in this module, instead of defining their own.
"""
import logging
import sys


logging.REPORT  = 25
logging.SIGNAL  = 15
logging.METRIC  = 13
logging.TICK    = 5
logging.addLevelName(logging.REPORT, 'REPORT')
logging.addLevelName(logging.SIGNAL, 'SIGNAL')
logging.addLevelName(logging.METRIC, 'METRIC')
logging.addLevelName(logging.TICK, 'TICK')


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



def defaultFormatter(notimestamp=False):
    """Gets the default formatter."""
    if notimestamp:
        fmt = '%(name)-10s [%(levelname)-8s] %(message)s'
    else:
        fmt = '%(name)-10s %(asctime)s [%(levelname)-8s] %(message)s'
    datefmt = '%Y-%m-%d %H:%M:%S'
    return logging.Formatter(fmt=fmt, datefmt=datefmt)

std_formatter = defaultFormatter


class DefaultFormatter(logging.Formatter):
    fmt = '%(name)-10s %(asctime)s %(levelname)-10s %(message)s'
    datefmt = '%Y-%m-%d %H:%M:%S'

    def __init__(self):
        super().__init__(fmt=self.fmt, datefmt=self.datefmt)

    def format(self, record):
        record.levelname = '[' + record.levelname + ']'
        s = super().format(record)
        return s


class ColorFormatter(logging.Formatter):
    """Formatter that colors the levelname and logged message."""
    fmt = '%(name)-10s %(asctime)s %(levelname)-19s %(message)s'
    datefmt = '%Y-%m-%d %H:%M:%S'

    RESET   = '\033[0m'
    COLOR   = '\033[%dm'
    RED     = COLOR % 31
    YELLOW  = COLOR % 33
    GREEN   = COLOR % 32
    BLUE    = COLOR % 34

    def __init__(self):
        super().__init__(fmt=self.fmt, datefmt=self.datefmt)

    def format(self, record):
        self._format_levelname(record)
        self._format_name(record)
        s = super().format(record)
        return s

    def _format_levelname(self, record):
        color = self._get_color(record)
        record.levelname = color + record.levelname + self.RESET
        record.levelname = '[' + record.levelname + ']'
        return record

    def _format_name(self, record):
        record.name = record.name.capitalize()
        return record

    def _get_color(self, record):
        if record.levelno >= logging.ERROR:
            return self.RED
        elif record.levelno >= logging.WARNING:
            return self.YELLOW
        elif record.levelno >= logging.INFO:
            return self.GREEN
        else:
            return self.BLUE


def make_logger(name, *handlers, level=logging.DEBUG):
    """Attach handles to new logger"""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    for h in handlers:
        logger.addHandler(h)
    return logger


def get_filehandler(fname, level=logging.DEBUG, formatter=DefaultFormatter()):
    fh = logging.FileHandler(fname)
    fh.setLevel(level)
    fh.setFormatter(formatter)
    return fh


def get_streamhandler(stream=sys.stdout, level=logging.INFO, formatter=ColorFormatter()):
    sh = logging.StreamHandler(stream=sys.stdout)
    sh.setLevel(level)
    sh.setFormatter(formatter)
    return sh

"""
This module defines custom log levels for trading events, monkey patch the
standard logging module, and provide logging related helpers. The custom level
sare all defined with severity below logging.WARNING as listed:

- REPORT  25
- SIGNAL  15
- METRIC  13
- TICK    5

When cryptle.logging is imported in any one of the modules in a python
application, loggers created from logging.getLogger will be monkey patched to
have a log method for each corresponding log level described above. Cryptle
internally uses `str.format()
<https://docs.python.org/3/library/string.html#formatstrings>`_ format string
syntax for log messages. Hence the method `getMessage
<https://docs.python.org/3/library/logging.html#logging.LogRecord.getMessage>`_
of LogRecord is monkey patched as well.

Default formatters subclassed from `logging.Formatter
<https://docs.python.org/3/library/logging.html#logging.Formatter>`_ provide a
unified log format for cryptle. A number of helper functions setup the root
logger with sensible defaults, tailored for paper-trading and live-trading.
"""
import logging
import sys


logging.REPORT = 25
logging.SIGNAL = 15
logging.METRIC = 13
logging.TICK = 5
logging.addLevelName(logging.REPORT, 'REPORT')
logging.addLevelName(logging.SIGNAL, 'SIGNAL')
logging.addLevelName(logging.METRIC, 'METRIC')
logging.addLevelName(logging.TICK, 'TICK')

# Logging level largely referenced from the python standard library
CRITICAL = 50
FATAL = CRITICAL
ERROR = 40
WARNING = 30
WARN = WARNING
INFO = 20
DEBUG = 10
NOTSET = 0

# Self-defined logging level
logging.REPORT = REPORT = 25
logging.SIGNAL = SIGNAL = 15
logging.METRIC = METRIC = 13
logging.TICK = TICK = 5

# Following cookbook recipe
library_factory = logging.getLogRecordFactory()

# This would provide the callable to replace the _logRecordFactory
def record_factory(*args, **kwargs):
    new_factory = library_factory
    new_factory.getMessage = _logrecord_getmessage_fix
    return new_factory(*args, **kwargs)


_logRecordFactory = record_factory

# This is essential to use module _logRecordFactory defined instead of overwriting the
# one in library


logging.addLevelName(SIGNAL, 'SIGNAL')


class Logger(logging.Logger):

    def __init__(self):
        super().__init__()

    # Monkey patching library_logger's makeRecord method to use the factory
    def makeRecord(
        self, name, level, fn, lno, msg, args, exc_info, func=None, extra=None, sinfo=None
    ):
        """
        A factory method which can be overridden in subclasses to create
        specialized LogRecords.
        """
        rv = _logRecordFactory(name, level, fn, lno, msg, args, exc_info, func, sinfo)
        if extra is not None:
            for key in extra:
                if (key in ["message", "asctime"]) or (key in rv.__dict__):
                    raise KeyError("Attempt to overwrite %r in LogRecord" % key)
                rv.__dict__[key] = extra[key]
        return rv

# Should be different but smae for now
print(id(Logger))
print(id(logging.Logger))

# Should be different but smae for now
print(id(Logger.makeRecord))
print(id(logging.Logger.makeRecord))

FileHandler = logging.FileHandler
StreamHandler = logging.StreamHandler


def getLogger(name=None):
    if name:
        return Logger.manager.getLogger(name)
    else:
        return logging.RootLogger(logging.WARNING)


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


logging.Logger.signal = _signal
logging.Logger.report = _report
logging.Logger.metric = _metric
logging.Logger.tick = _tick
# Monkey patch LogRecord.getMessage() method in logging module
def _logrecord_getmessage_fix(self):
    msg = str(self.msg)
    if self.args:
        msg = msg.format(*self.args)
    return msg


logging.LogRecord.getMessage = _logrecord_getmessage_fix


class DebugFormatter(logging.Formatter):
    """Create detailed and machine parsable log messages."""

    fmt = '{asctime}:{levelname}:{filename}:{lineno}:{message}'
    datefmt = '%Y%m%dT%H%M%S'

    def __init__(self, **kwargs):
        super().__init__(fmt=self.fmt, datefmt=self.datefmt, style='{', **kwargs)


class SimpleFormatter(logging.Formatter):
    """Create readable basic log messages."""

    fmt = '{name:<12} {levelname:<8} {message}'
    datefmt = '%Y%m%dT%H%M%S'

    def __init__(self, **kwargs):
        super().__init__(fmt=self.fmt, datefmt=self.datefmt, style='{', **kwargs)

    def format(self, record):
        record.levelname = '[' + record.levelname + ']'
        s = super().format(record)
        return s


class ColorFormatter(logging.Formatter):
    """Create colorize log messages with terminal control characters."""

    fmt = '{name:<10} {asctime} {levelname:<8} {message}'
    datefmt = '%Y-%m-%d %H:%M:%S'

    RESET = '\033[0m'
    COLOR = '\033[%dm'
    RED = COLOR % 31
    YELLOW = COLOR % 33
    GREEN = COLOR % 32
    BLUE = COLOR % 34

    def __init__(self, **kwargs):
        super().__init__(fmt=self.fmt, datefmt=self.datefmt, style='{', **kwargs)

    def format(self, record):
        self._format_levelname(record)
        s = super().format(record)
        return s

    def _format_levelname(self, record):
        color = self._get_color(record)
        record.levelname = color + record.levelname + self.RESET
        record.levelname = '[' + record.levelname + ']'
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


def get_filehandler(fname, level=logging.DEBUG, formatter=DebugFormatter()):
    fh = logging.FileHandler(fname)
    fh.setLevel(level)
    fh.setFormatter(formatter)
    return fh


def get_streamhandler(
    stream=sys.stdout, level=logging.INFO, formatter=ColorFormatter()
):
    sh = logging.StreamHandler(stream=sys.stdout)
    sh.setLevel(level)
    sh.setFormatter(formatter)
    return sh


def configure_root_logger(file, flvl=logging.DEBUG, slvl=logging.REPORT) -> None:
    """Helper routine to setup root logger with file and stream handlers.

    Adds a file handler and stream handler to the root logger. These handlers
    are configured to use standard formatters in cryptle.

    Args
    ----
    file : str
        Log file's name
    flvl:
        Log level of the file handler
    slvl:
        Log level of the stream handler

    """
    fh = logging.FileHandler('papertrade.log', mode='w')
    fh.setLevel(flvl)
    fh.setFormatter(cryptle.logging.DebugFormatter())

    sh = logging.StreamHandler()
    sh.setLevel(slvl)
    sh.setFormatter(cryptle.logging.ColorFormatter())

    root = logging.getLogger()
    root.addHandler(sh)
    root.addHandler(fh)
    root.setLevel(flvl)

"""
This module provides package-wide logging facility and defines custom log levels for
trading events.

The implementation of the package Logger largely based on the `standard logging library
of python <https://docs.python.org/3.5/logging.html>`_. The principle of this extensive
patching approach is to exercise the developers preferences to logging while
simultaneously preserving the integrity of standard library source that other
third-party libraries might depend on.

The custom level share all defined with severity below logging.WARNING as listed:

- REPORT  25
--INFO    20--
- SIGNAL  15
- METRIC  13
- TICK    5

When cryptle.logging is imported in any one of the modules in a python application,
loggers created from cryptle.logging.getLogger will, in addition to the standard logging
facilities provided by the standard, extra log method for each corresponding log level
described above. Users are suggested to use cryptle.logging universally for logging when
developing in the Cryptle framework. Uses of the standard logging libary is discouraged.

Cryptle internally uses `str.format()
<https://docs.python.org/3/library/string.html#formatstrings>`_ format string syntax for
log messages. To encapsulate and limit this change to the package level, a Logger class
and related structures of the standard library are subclassed and patched.

Default formatters subclassed from `logging.Formatter
<https://docs.python.org/3/library/logging.html#logging.Formatter>`_ provide a
unified log format for cryptle. A number of helper functions setup the root
logger with sensible defaults.
"""
import logging
import threading
import sys


# --------------------------------------------------------------------------------------
#   Adoption of standard python logging library Logger to cryptle.logging.Logger
# --------------------------------------------------------------------------------------

# Logging level referenced from the python standard library
CRITICAL = 50
FATAL = CRITICAL
ERROR = 40
WARNING = 30
WARN = WARNING
INFO = 20
DEBUG = 10
NOTSET = 0

# Self-defined logging level
# Todo(MC): Consider whether to add this to source or to package instead
logging.REPORT = REPORT = 25
logging.SIGNAL = SIGNAL = 15
logging.METRIC = METRIC = 13
logging.TICK = TICK = 5

logging.addLevelName(REPORT, 'REPORT')
logging.addLevelName(SIGNAL, 'SIGNAL')
logging.addLevelName(METRIC, 'METRIC')
logging.addLevelName(TICK, 'TICK')


class LogRecord(logging.LogRecord):
    def getMessage(self):
        msg = str(self.msg)
        if self.args:
            msg = msg.format(*self.args)
        return msg


class Logger(logging.Logger):
    def makeRecord(
        self,
        name,
        level,
        fn,
        lno,
        msg,
        args,
        exc_info,
        func=None,
        extra=None,
        sinfo=None,
    ):
        """
        Overriden method of the logging.Logger with modified record_factory
        """

        rv = LogRecord(name, level, fn, lno, msg, args, exc_info, func, sinfo)
        if extra is not None:
            for key in extra:
                if (key in ["message", "asctime"]) or (key in rv.__dict__):
                    raise KeyError("Attempt to overwrite %r in LogRecord" % key)
                rv.__dict__[key] = extra[key]
        return rv


FileHandler = logging.FileHandler
StreamHandler = logging.StreamHandler


def getLogger(name=None):
    if name:
        return Logger.manager.getLogger(name)
    else:
        return root


# Threading-related stuff
if threading:
    _lock = threading.RLock()
else:  # pragma: no cover
    _lock = None


_acquireLock = logging._acquireLock
_releaseLock = logging._releaseLock


# Custom manager
class Manager(logging.Manager):
    def __init__(self, rootnode):
        super().__init__(rootnode)

    # For patching references to Logger
    def getLogger(self, name):
        """Semantically equivalent to standard logging"""
        rv = None
        if not isinstance(name, str):
            raise TypeError('A logger name must be a string')
        _acquireLock()
        try:
            if name in self.loggerDict:
                rv = self.loggerDict[name]
                if isinstance(rv, PlaceHolder):
                    ph = rv
                    rv = (self.loggerClass or Logger)(name)
                    rv.manager = self
                    self.loggerDict[name] = rv
                    self._fixupChildren(ph, rv)
                    self._fixupParents(rv)
            else:
                rv = (self.loggerClass or Logger)(name)
                rv.manager = self
                self.loggerDict[name] = rv
                self._fixupParents(rv)
        finally:
            _releaseLock()
        return rv

    # For patching references to Placeholder
    def _fixupParents(self, alogger):
        """Semantically equivalent to standard logging"""
        name = alogger.name
        i = name.rfind(".")
        rv = None
        while (i > 0) and not rv:
            substr = name[:i]
            if substr not in self.loggerDict:
                self.loggerDict[substr] = PlaceHolder(alogger)
            else:
                obj = self.loggerDict[substr]
                if isinstance(obj, Logger):
                    rv = obj
                else:
                    assert isinstance(obj, PlaceHolder)
                    obj.append(alogger)
            i = name.rfind(".", 0, i - 1)
        if not rv:
            rv = self.root
        alogger.parent = rv


# For giving custom Logger instance a custom Manger
root = logging.root
Logger.root = root
Logger.manager = Manager(Logger.root)


class PlaceHolder(logging.PlaceHolder):
    pass


def _report(self, message, *args, **kargs):
    if self.isEnabledFor(REPORT):
        self._log(REPORT, message, args, **kargs)


def _signal(self, message, *args, **kargs):
    if self.isEnabledFor(SIGNAL):
        self._log(SIGNAL, message, args, **kargs)


def _metric(self, message, *args, **kargs):
    if self.isEnabledFor(METRIC):
        self._log(METRIC, message, args, **kargs)


def _tick(self, message, *args, **kargs):
    if self.isEnabledFor(TICK):
        self._log(TICK, message, args, **kargs)


# Todo(MC): Consider whether to add this to source or to package instead
logging.Logger.signal = _signal
logging.Logger.report = _report
logging.Logger.metric = _metric
logging.Logger.tick = _tick

# --------------------------------------------------------------------------------------


class DebugFormatter(logging.Formatter):
    """Create detailed and machine parsable log messages."""

    fmt = '{asctime}:{levelname}:{name}:{filename}:{lineno}:{message}'
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
        if record.levelno >= ERROR:
            return self.RED
        elif record.levelno >= WARNING:
            return self.YELLOW
        elif record.levelno >= INFO:
            return self.GREEN
        else:
            return self.BLUE


def make_logger(name, *handlers, level=DEBUG):
    """Attach handles to new logger"""
    logger = getLogger(name)
    logger.setLevel(level)
    for h in handlers:
        logger.addHandler(h)
    return logger


def get_filehandler(fname, level=DEBUG, formatter=DebugFormatter()):
    fh = FileHandler(fname, mode='w')
    fh.setLevel(level)
    fh.setFormatter(formatter)
    return fh


def get_streamhandler(stream=sys.stdout, level=INFO, formatter=ColorFormatter()):
    sh = StreamHandler(stream=sys.stdout)
    sh.setLevel(level)
    sh.setFormatter(formatter)
    return sh


def configure_root_logger(
    file=None, stream=sys.stdout, file_level=DEBUG, stream_level=REPORT
) -> None:
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
    if file:
        fh = get_filehandler(file, level=file_level)
        root.addHandler(fh)

    sh = get_streamhandler(stream, level=stream_level)
    root.addHandler(sh)
    root.setLevel(file_level if file_level < stream_level else stream_level)

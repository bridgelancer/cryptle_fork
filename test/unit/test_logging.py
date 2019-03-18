"""Test suite for custom derived logging

Important patching aspects of the custom Logger and the related logging features
provided in the cryptle.logging would be tested. Capturing of logs from pytest would be
supported.

"""

import logging
import inspect
from pathlib import Path

import cryptle.logging
from cryptle.aggregator import Aggregator


# Todo(MC): consider fixture and parameterization of tests
logger = cryptle.logging.getLogger('cryptle')

logger.setLevel(logging.TICK)

fh = cryptle.logging.FileHandler('logging.log', mode='w')
fh.setLevel(logging.TICK)

sh = cryptle.logging.StreamHandler()
sh.setLevel(logging.TICK)

logger.addHandler(fh)
logger.addHandler(sh)


def test_root():
    assert isinstance(cryptle.logging.root, logging.RootLogger)


def test_logger():
    assert isinstance(logger, cryptle.logging.Logger)
    assert issubclass(cryptle.logging.Logger, logging.Logger)


def test_manager():
    assert isinstance(logger.manager, cryptle.logging.Manager)
    assert issubclass(cryptle.logging.Manager, logging.Manager)


def test_class_patching():
    objs_patched = [logger.__class__, logger.__class__.manager.__class__]

    assert all(
        [Path(inspect.getfile(obj)).match('cryptle/logging.py') for obj in objs_patched]
    )


def test_logger_patching():
    objs_patched = [logger.manager.getLogger, logger.manager._fixupParents]

    assert all(
        [Path(inspect.getfile(obj)).match('cryptle/logging.py') for obj in objs_patched]
    )


def test_fstring_format(caplog):
    hi = 'world'
    f = 'work'

    logger.error(f'abc {hi}')
    for record in caplog.records:
        assert record.message == 'abc world'


def test_standard_integrity(caplog, capsys):
    logging.error('abc {}', 'world')  # not working
    for record in caplog.records:
        if 'message' in record.__dict__:
            raise AttributeError('Should not successfully format')
    out, err = capsys.readouterr()
    assert err.startswith('--- Logging error ---')

    caplog.clear()
    logging.error('abc %s', 'world')  # c-style formatting works
    for record in caplog.records:
        assert record.message == 'abc world'


# Todo(MC): Could consider parametrize to all cryptle module to test logging integrity
def test_propagation(caplog):
    a = Aggregator(100)
    a.pushTick([1, 2, 3, 4])

    for record in caplog.records:
        assert record.name == 'cryptle.aggregator'
        assert record.filename == 'aggregator.py'
        assert record.levelname == 'DEBUG'


# Test all custom made levels functionality
def test_levels(caplog):
    logger.signal('Testing signal...')
    logger.report('Testing report...')
    logger.metric('Testing metric...')
    logger.tick('Testing tick...')

    levels = ['SIGNAL', 'REPORT', 'METRIC', 'TICK']

    assert [record.levelname for record in caplog.records] == levels


# Test all custom formatters
def test_formatters(caplog):
    hi = 'world'
    simple = cryptle.logging.SimpleFormatter
    debug = cryptle.logging.DebugFormatter
    color = cryptle.logging.ColorFormatter

    sh.setFormatter(simple())
    logger.warning(f'abc {hi}')
    sh.setFormatter(debug())
    logger.warning(f'abc {hi}')
    sh.setFormatter(color())
    logger.warning(f'abc {hi}')

    levels = ['[WARNING]', 'WARNING', '[\x1b[33mWARNING\x1b[0m]']

    assert [record.levelname for record in caplog.records] == levels


# Test all configure root logger functionality
def test_configure_root_logger(caplog):
    hi = 'world'
    # By default no file and stream handler
    cryptle.logging.root.warning(f'abc {hi}')

    # After configuring, have file and stream handler
    cryptle.logging.configure_root_logger('logging.log')
    cryptle.logging.root.warning(f'abc {hi}')

    levels = ['WARNING', '[\x1b[33mWARNING\x1b[0m]']

    assert [record.levelname for record in caplog.records] == levels

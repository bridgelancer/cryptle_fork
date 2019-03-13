import logging
import inspect
from pathlib import Path

import cryptle.logging
from cryptle.aggregator import Aggregator


# Todo(MC): consider fixture
logger = cryptle.logging.getLogger('cryptle')

logger.setLevel(cryptle.logging.DEBUG)

fh = cryptle.logging.FileHandler('logging.log', mode='w')
fh.setLevel(cryptle.logging.DEBUG)

sh = cryptle.logging.StreamHandler()
sh.setLevel(cryptle.logging.DEBUG)

logger.addHandler(fh)
logger.addHandler(sh)


def test_root():
    assert isinstance(cryptle.logging.root, cryptle.logging.RootLogger)
    assert issubclass(cryptle.logging.RootLogger, logging.RootLogger)


def test_logger():
    assert isinstance(logger, cryptle.logging.Logger)
    assert issubclass(cryptle.logging.Logger, logging.Logger)


def test_manager():
    assert isinstance(logger.manager, cryptle.logging.Manager)
    assert issubclass(cryptle.logging.Manager, logging.Manager)


def test_class_patching():
    objs_patched = [
        logger.__class__,
        logger.__class__.manager.__class__,
    ]

    assert all(
        [Path(inspect.getfile(obj)).match('cryptle/logging.py') for obj in objs_patched]
    )

def test_logger_patching():
    objs_patched = [
        logger.makeRecord,
        logger.manager.getLogger,
        logger.manager._fixupParents,
    ]

    assert all(
        [Path(inspect.getfile(obj)).match('cryptle/logging.py') for obj in objs_patched]
    )

def test_fstring_format():
    pass


def test_levels():
    pass


def test_formatters():
    pass


def test_filehandler():
    pass


def test_streamhandler():
    pass


def test_configure_root_logger():
    pass

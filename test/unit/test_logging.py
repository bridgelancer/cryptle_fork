import cryptle.logging as logging
import inspect
from pathlib import Path
from cryptle.aggregator import Aggregator

logger = logging.getLogger('cryptle')


print(logger)
logger.setLevel(logging.DEBUG)

fh = logging.FileHandler('logging.log', mode='w')
fh.setLevel(logging.DEBUG)

sh = logging.StreamHandler()
sh.setLevel(logging.DEBUG)

logger.addHandler(fh)
logger.addHandler(sh)


def test_class_patching():
    objs_patched = []


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

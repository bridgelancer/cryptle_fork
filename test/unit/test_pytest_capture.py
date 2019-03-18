import logging
import cryptle.logging as clogging

logger = logging.getLogger('test')
clogger = clogging.getLogger('ctest')

# Previous root logger changes would affect the logger in this run - consider
# encapulation such as fixture in test_logging.


def test_naive(caplog):
    logger.error('testing pytest capturing for standard library')
    if not caplog.records:
        assert False
    for record in caplog.records:
        assert record.name == 'test'
        assert record.message == 'testing pytest capturing for standard library'
        assert record.module == 'test_pytest_capture'


def test_cryptle_logging_capture(caplog):
    clogger.error('testing pytest capturing for cryptle logging')
    if not caplog.records:
        assert False
    for record in caplog.records:
        assert record.name == 'ctest'
        assert record.message == 'testing pytest capturing for cryptle logging'
        assert record.module == 'test_pytest_capture'

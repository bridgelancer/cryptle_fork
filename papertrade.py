from cryptle.datafeed import Bitstamp
from cryptle.exchange import Paper
from cryptle.backtest import Backtest
from cryptle.strategy import Portfolio
import cryptle.logging
import cryptle.runtime as run

import sys
import logging
from collections import OrderedDict

from pivot import default_setup


def get_logger(flvl=logging.DEBUG, slvl=logging.REPORT):
    fh = logging.FileHandler('papertrade.log', mode='w')
    fh.setLevel(flvl)

    sh = logging.StreamHandler()
    sh.setLevel(slvl)

    logger = logging.getLogger('papertrade')
    logger.addHandler(sh)
    logger.addHandler(fh)
    logger.setLevel(flvl)

    return logger, (fh, sh)


def final_report(logger, strat):
    port = strat.portfolio
    logger.report('Equity:  {}', port.equity({'btc': strat.registry.current_price}))
    logger.report('Cash:    {}', port.cash)
    logger.report('Asset:   {}', str(port.balance))
    logger.report('No. of candles:  {}', strat.registry.num_bars)


def main():
    logger, handlers = get_logger()
    strat, (bus, exchange) = default_setup()

    feed = Bitstamp()
    bus.bind(feed)

    TRADE_EVENT = 'trades:btcusd'
    feed.connect()
    feed.broadcast(TRADE_EVENT)

    run.listen_for_interrupt_forever()
    final_report(logger, strat)


if __name__ == '__main__':
    sys.exit(main())

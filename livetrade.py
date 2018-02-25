from cryptle.datafeed import connect
from cryptle.exchange import Bitstamp
from cryptle.strategy import Portfolio
from cryptle.loglevel import *

from cryptle.runtime  import Runtime

from macdsnb_v2 import SNBStrat

import pprint
import logging
import sys
from datetime import datetime as dt
from collections import OrderedDict


def setup_loggers(fname):
    formatter = defaultFormatter()

    sh = logging.StreamHandler()
    sh.setLevel(logging.INFO)
    sh.setFormatter(formatter)

    fh = logging.FileHandler(fname, mode='w')
    fh.setLevel(logging.TICK)
    fh.setFormatter(formatter)

    log = logging.getLogger('Runtime')
    log.setLevel(logging.DEBUG)
    log.addHandler(sh)
    log.addHandler(fh)

    stlog = logging.getLogger('Strategy')
    stlog.setLevel(logging.DEBUG)
    stlog.addHandler(sh)
    stlog.addHandler(fh)

    crlog = logging.getLogger('cryptle')
    crlog.setLevel(logging.DEBUG)
    crlog.addHandler(sh)
    crlog.addHandler(fh)

    return log


if __name__ == '__main__':
    asset = 'bch'
    base_currency = 'usd'
    log_file = 'livetrade.' + dt.today().strftime('%Y%m%d-%H%M') + '.log'

    # Set up logger
    log = setup_loggers(log_file)
    log.report('Logging to ' + log_file)

    # Load private keys from command line args
    log.debug('Initialising private keys...')
    key     = sys.argv[1]
    secret  = sys.argv[2]
    cid     = sys.argv[3]
    exchange = Bitstamp(key, secret, cid)

    # Retrieve balance from exchange
    log.debug('Retrieving balance...')
    balance = exchange.getBalance()

    # Set up portfolio
    log.debug('Initialising portfolio...')
    port = Portfolio(balance=balance, base_currency=base_currency)

    log.debug('Initialising strategy...')

    config = {
        'period': 120,
        'bband': 6.5,
        'bband_period': 20,
        'bwindow': 3600,
        'snb_factor': 1.25,
        'snb_bband': 1.25,
        'rsi_thresh': 40,
        'equity_at_risk': 0.95
    }

    strat = SNBStrat(**config, asset=asset, base_currency=base_currency, portfolio=port, exchange=exchange)

    # Log the configuration
    ordered_config = OrderedDict(sorted(config.items(), key=lambda k: k[0]))
    log.report('Config: \n{}'.format(pprint.pformat(ordered_config, indent=4)))


    with connect('bitstamp') as feed:
        log.debug('Initialising data feed and callbacks...')
        feed.onTrade(asset, base_currency, lambda x: strat.pushTick(*unpackTick(x)))

        loop = Runtime(strat, exchange, log)
        loop.run_forever()

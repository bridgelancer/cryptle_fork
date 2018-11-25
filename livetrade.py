from cryptle.datafeed import Bitstamp as Feed
from cryptle.exchange import Bitstamp as Exchange
from cryptle.strategy import Portfolio
import cryptle.logging

from cryptle.runtime  import Runtime

import sys
import logging
from datetime import datetime as dt


if __name__ == '__main__':
    asset = 'bch'
    base_currency = 'usd'
    log_file = 'livetrade.' + dt.today().strftime('%Y%m%d-%H%M') + '.log'

    # Set up logger
    log = setup_loggers(log_file)
    log.report('Logging to ' + log_file)

    # Todo: Advanced parameter loading
    # Try loading from with the following precedence
    # cli args > env vars

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
    port = Portfolio(balance=balance, base_currency=base_currency)

    with connect('bitstamp') as feed:
        log.debug('Initialising data feed and callbacks...')
        feed.onTrade(asset, base_currency, lambda x: strat.pushTick(*unpackTick(x)))

        loop = Runtime(strat, exchange)
        loop.run_forever()

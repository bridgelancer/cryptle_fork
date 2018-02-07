from cryptle.datafeed import BitstampFeed
from cryptle.exchange import Bitstamp
from cryptle.strategy import Portfolio
from cryptle.loglevel import *
from cryptle.utility  import *

from wmamacdrsi import WMAMACDRSIStrat

import logging
import sys
import time
import json
from collections import OrderedDict


if __name__ == '__main__':
    formatter = defaultFormatter()

    sh = logging.StreamHandler()
    sh.setLevel(logging.INFO)
    sh.setFormatter(formatter)

    fh = logging.FileHandler('livetrade.log', mode='w')
    fh.setLevel(logging.TICK)
    fh.setFormatter(formatter)

    log = logging.getLogger('Report')
    log.setLevel(logging.TICK)
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

    log.report('Logging to ' + fh.baseFilename)

    log.debug('Initialising REST private parameters...')
    key = sys.argv[1]
    secret = sys.argv[2]
    cid = sys.argv[3]
    exchange = Bitstamp(key, secret, cid)
    pair = 'bchusd'

    log.debug('Retrieving balance...')
    full_balance = exchange.getBalance()
    pair_value = exchange.getTicker(pair)

    log.debug('Initialising portfolio...')
    pair_available = pair[:3] + '_available'
    cash = float(full_balance['usd_available'])
    balance = {pair: float(full_balance[pair_available])}
    balance_value = {pair: balance[pair] * float(pair_value['last'])}

    if balance[pair] != 0:
        port = Portfolio(cash, balance, balance_value)
    else:
        port = Portfolio(cash)


    config = OrderedDict()
    config['period']        = period = 120
    config['bband']         = bband = 6.0
    config['bband_period']  = bband_period = 20
    config['timeframe']     = timeframe = 3600
    config['equity@risk']   = equity_at_risk = 0.9

    log.debug('Initialising strategy...')
    log.report('Config: {}'.format(config))

    wma = WMAMACDRSIStrat(
            period=period,
            bband=bband,
            bband_period=bband_period,
            timeframe=timeframe,
            pair=pair,
            portfolio=port,
            exchange=exchange,
            equity_at_risk=equity_at_risk)


    log.debug('Initialising data feed and callbacks...')
    bs = BitstampFeed()
    bs.onTrade(pair, lambda x: wma.pushTick(*unpackTick(x)))

    log.debug('Reporting started')
    while bs.isConnected():
        log.report('Equity:  {}'.format(port.equity))
        log.report('Cash:    {}'.format(port.cash))
        log.report('Balance: {}'.format(port.balance))

        time.sleep(60)
        port.cash = exchange.getCash()


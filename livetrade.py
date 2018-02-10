from cryptle.datafeed import BitstampFeed
from cryptle.exchange import Bitstamp
from cryptle.strategy import Portfolio
from cryptle.loglevel import *
from cryptle.utility  import *

from macdsnb_v2 import SNBStrat

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

    port = Portfolio(cash, balance, balance_value)


    config = OrderedDict()
    config['period']        = period = 120
    config['bband']         = bband = 6.0
    config['bband_period']  = bband_period = 20
    config['bband_window']  = bband_window = 3600
    config['snb_factor']    = snb_factor = 1.25
    config['snb_bband']     = snb_bband = 3.0
    config['equity@risk']   = equity_at_risk = 0.95

    log.debug('Initialising strategy...')
    log.report('Config: \n{}'.format(json.dumps(config, indent=4)))

    strat = SNBStrat(
            period=period,
            bband=bband,
            bband_period=bband_period,
            bwindow=bband_window,
            snb_factor=snb_factor,
            snb_bband=snb_bband,
            pair=pair,
            portfolio=port,
            exchange=exchange,
            equity_at_risk=equity_at_risk)


    log.debug('Initialising data feed and callbacks...')
    bs = BitstampFeed()
    bs.onTrade(pair, lambda x: strat.pushTick(*unpackTick(x)))

    log.debug('Reporting started')
    while bs.isConnected():
        log.report('Equity:  {}'.format(port.equity))
        log.report('Cash:    {}'.format(port.cash))
        log.report('Balance: {}'.format(port.balance))

        time.sleep(60)

        pair_value = exchange.getTicker(pair)
        full_balance = exchange.getBalance()
        port.cash = float(full_balance['usd_available'])
        port.balance_value = {pair: port.balance[pair] * float(pair_value['last'])}

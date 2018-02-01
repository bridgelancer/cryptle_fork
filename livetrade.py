from cryptle.datafeed import BitstampFeed
from cryptle.exchange import Bitstamp
from cryptle.strategy import Portfolio
from cryptle.loglevel import *
from cryptle.utility  import *

from wmarsiobc import WMARSIOBCStrat

import logging
import sys
import time
import json


formatter = defaultFormatter()

sh = logging.StreamHandler()
sh.setLevel(logging.REPORT)
sh.setFormatter(formatter)

fh = logging.FileHandler('livetrade.log', mode='w')
fh.setLevel(logging.TICK)
fh.setFormatter(formatter)

log = logging.getLogger('Report')
log.setLevel(logging.TICK)
log.addHandler(sh)
log.addHandler(fh)

crlog = logging.getLogger('cryptle')
crlog.setLevel(logging.TICK)
crlog.addHandler(sh)
crlog.addHandler(fh)


def livetrade(key, secret, cid):
    log.debug('Initialising REST private parameters...')
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


    log.debug('Initialising strategy...')
    wma = WMARSIOBCStrat(
            period=120,
            bband=8.0,
            bband_period=20,
            timelag_required=0,
            pair=pair,
            portfolio=port,
            exchange=exchange,
            equity_at_risk=0.8)

    log.debug('Initialising data feed and callbacks...')
    bs = BitstampFeed()
    # Fix after changing bitstampfeed to output json
    bs.onTrade(pair, lambda x: wma.pushTick(*unpackTick(x)))


    log.debug('Reporting started')
    while bs.isConnected():
        log.report('Equity:  {}'.format(port.equity))
        log.report('Cash:    {}'.format(port.cash))
        log.report('Balance: {}'.format(port.balance))

        time.sleep(60)
        port.cash = exchange.getCash()


if __name__ == '__main__':
    key = sys.argv[1]
    secret = sys.argv[2]
    cid = sys.argv[3]
    livetrade(key, secret, cid)


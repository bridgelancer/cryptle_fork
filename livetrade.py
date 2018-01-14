from exchange import *
from datafeed import *
from strategy import *

import logging
import sys
import time


logging.TICK = 5
logging.addLevelName(logging.TICK, 'TICK')

fmt = '%(name)-10s| %(asctime)s [%(levelname)5s] %(message)s'
formatter = logging.Formatter(fmt, '%Y-%m-%d %H:%M:%S')

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)

fh = logging.FileHandler('livetrade.log', mode='w')
fh.setLevel(logging.TICK)
fh.setFormatter(formatter)

log = logging.getLogger('Report')
log.setLevel(logging.TICK)
log.addHandler(ch)
log.addHandler(fh)

crlog = logging.getLogger('Cryptle')
crlog.setLevel(logging.DEBUG)
crlog.addHandler(ch)
crlog.addHandler(fh)

exlog = logging.getLogger('Exchange')
exlog.setLevel(logging.DEBUG)
exlog.addHandler(ch)
exlog.addHandler(fh)


def livetrade(key, secret, cid):
    pair = 'bchusd'


    log.debug('Initialising REST parameters...')

    exchange = Bitstamp(key, secret, cid)


    log.debug('Retrieving balance...')

    full_balance = exchange.getBalance()
    pair_value = exchange.getTicker(pair)


    log.debug('Initialising portfolio...')

    pair_available = pair[:3] + '_available'
    cash = float(full_balance['usd_available'])
    balance = {pair: float(full_balance[pair_available])}

    balance_value = {pair: balance[pair] * float(pair_value['last'])}
    port = Portfolio(cash, balance, balance_value)


    log.debug('Initialising strategy...')

    wma = WMAModStrat(pair, port, exchange, period=180)


    log.debug('Initialising data feed and callbacks...')

    bs = BitstampFeed()
    bs.onTrade(pair, wma)
    bs.onTrade(pair, lambda x: log.log(logging.TICK, x))


    while True:
        log.info('Cash:    {}'.format(port.cash))
        log.info('Balance: {}'.format(port.balance))
        log.info('Equity:  {}'.format(port.equity()))

        time.sleep(60)


if __name__ == '__main__':
    key = sys.argv[1]
    secret = sys.argv[2]
    cid = sys.argv[3]
    livetrade(key, secret, cid)


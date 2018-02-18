from cryptle.datafeed import BitstampFeed
from cryptle.exchange import Bitstamp
from cryptle.strategy import Portfolio
from cryptle.loglevel import *
from cryptle.utility  import *

from macdsnb_v2 import SNBStrat

import pprint
import logging
import sys
import time
import threading
from collections import OrderedDict

terminated = False
help_text = (
    '\n'
    'Cryptle live trade\n'
    'h   Print this help\n'
    'r   Report current portfolio status\n'
    'l   List available strategy attributes\n'
    'q   Stop trading\n'
    '<attribute> Print the value of <attribute>\n'
)

# @Hardcoded instructions/attributes
# String is returned in case of future usage of other output devices (i.e. website)
def handle_input(line, strat):
    line = line[:-1]
    if line == 'h':
        return help_text

    elif line == 'r':
        p = strat.portfolio
        return 'Equity:  {}\nCash:    {}\nBalance: {}\n'.format(p.equity, p.cash, p.balance)

    elif line == 'l':
        return pprint.pformat(list(strat.__dict__.keys()), indent=4)

    elif line == 'exit' or line == 'quit' or line == 'q':
        raise KeyboardInterrupt

    else:
        try:
            return strat.__dict__[line]
        except KeyError:
            return 'Attribute does not exist'

# @Shit design @Bad dependence
def main_loop(pair, port, log, feed, exchange):
    s = 0
    while feed.isConnected() and not terminated:
        time.sleep(1)
        s += 1
        s %= 3
        if s == 0:
            # @Shit code: Think of new interface
            prices = {pair['asset']: float(exchange.getTicker(**pair)['last'])}
            balance = exchange.getBalance()

#            if (port.cash != balance[pair[1]]
#                or balance[pair[1]] != port.balance[pair[1]]
#            ):
                #port.cash = pair_value['last']
                #port.balance[pair[1]] = balance[pair[1]]
            port.updateEquity(prices)
            port.balance.update(balance)
            log.report('Equity:  {}'.format(port.equity))
            log.report('Cash:    {}'.format(port.cash))
            log.report('Balance: {}'.format(port.balance))


def setup_loggers(fname):
    formatter = defaultFormatter()

    sh = logging.StreamHandler()
    sh.setLevel(logging.INFO)
    sh.setFormatter(formatter)

    fh = logging.FileHandler(fname, mode='w')
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

    return log


if __name__ == '__main__':
    pair = {
        'asset': 'bch',
        'base_currency': 'usd'
    }

    log_file = 'livetrade.log'
    config_file = 'livetrade.config'

    config_fh = logging.FileHandler(config_file, mode='w')
    config_fh.setLevel(logging.INFO)
    config_fh.setFormatter(logging.Formatter(fmt='%(message)s'))

    cfglog = logging.getLogger('config')
    cfglog.setLevel(logging.DEBUG)
    cfglog.addHandler(config_fh)

    log = setup_loggers(log_file)
    log.report('Logging to ' + log_file)

    log.debug('Initialising private keys...')
    key     = sys.argv[1]
    secret  = sys.argv[2]
    cid     = sys.argv[3]
    exchange = Bitstamp(key, secret, cid)

    log.debug('Retrieving balance...')
    balance = exchange.getBalance()
    pair_value = exchange.getTicker(**pair)

    log.debug('Initialising portfolio...')
    port = Portfolio(balance=balance, base_currency=pair['base_currency'])

    log.debug('Initialising strategy...')
    config = OrderedDict()
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
    strat = SNBStrat(**config, **pair, portfolio=port, exchange=exchange)
    ordered_config = OrderedDict(sorted(config.items(), key=lambda k: k[0]))
    cfglog.report('Config: \n{}'.format(pprint.pformat(ordered_config, indent=4)))

    log.debug('Initialising data feed and callbacks...')
    feed = BitstampFeed()
    feed.onTrade(pair['asset'], pair['base_currency'], lambda x: strat.pushTick(*unpackTick(x)))

    log.debug('Reporting started')
    print(help_text)
    log.report('Equity:  {}'.format(port.equity))
    log.report('Cash:    {}'.format(port.cash))
    log.report('Balance: {}'.format(port.balance))

    main_thread = threading.Thread(target=main_loop, args=(pair, port, log, feed, exchange))
    main_thread.start()

    try:
        for line in sys.stdin:
            if line:
                s = handle_input(line, strat)
                print(s)
    except KeyboardInterrupt:
        print('Termination request received')
    finally:
        print('Terminating main loop...')
        terminated = True
        main_thread.join()

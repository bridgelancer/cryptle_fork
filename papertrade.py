from cryptle.datafeed import BitstampFeed
from cryptle.backtest import Backtest, PaperExchange
from cryptle.strategy import Portfolio
from cryptle.loglevel import *
from cryptle.utility import *

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
    'l   List available strategy attributes\n'
    'q   Stop trading\n'
    '<attribute> Print the value of <attribute>\n'
)


def handle_input(line, strat):
    line = line[:-1]
    if line == 'h':
        return help_text

    # @Use memotization
    elif line == 'l':
        return pprint.pformat(list(strat.__dict__.keys()), indent=4)

    elif line == 'exit' or line == 'quit' or line == 'q':
        raise KeyboardInterrupt

    else:
        try:
            return strat.__dict__[line]
        except KeyError:
            return 'Attribute does not exist'


def main_loop(port, log):
    s = 0
    while bs.isConnected() and not terminated:
        time.sleep(1)
        s += 1
        s %= 60
        if s == 0:
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
    pair     = 'bchusd'
    log_file = 'papertrade.log'

    log = setup_loggers(log_file)
    log.report('Logging to ' + log_file)

    log.debug('Initialising exchange...')
    exchange = PaperExchange(commission=0.12, slippage=0)

    log.debug('Initialising portfolio...')
    port = Portfolio(10000)

    log.debug('Initialising strategy...')
    config = OrderedDict()
    config['period']        = period = 120
    config['bband']         = bband = 6.0
    config['bband_period']  = bband_period = 20
    config['bband_window']  = bband_window = 3600
    config['snb_factor']    = snb_factor = 1.25
    config['snb_bband']     = snb_bband = 3.0
    config['equity@risk']   = equity_at_risk = 0.95
    log.report('Config: \n{}'.format(pprint.pformat(config, indent=4)))

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
    print(help_text)
    log.report('Equity:  {}'.format(port.equity))
    log.report('Cash:    {}'.format(port.cash))
    log.report('Balance: {}'.format(port.balance))

    main_thread = threading.Thread(target=main_loop, args=(port, log))
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

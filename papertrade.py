from cryptle.datafeed import *
from cryptle.exchange import *
from cryptle.strategy import Portfolio
from cryptle.loglevel import *
from wmamacdrsi import WMAMACDRSIStrat

import time
import logging
logger = logging.getLogger('Cryptle')
formatter = defaultFormatter()

sh = logging.StreamHandler()
sh.setLevel(logging.REPORT)
sh.setFormatter(formatter)

fh = logging.FileHandler('papertrade.log', mode='w')
fh.setLevel(logging.TICK)
fh.setFormatter(formatter)

logger = logging.getLogger('Backtest')
logger.setLevel(logging.DEBUG)
logger.addHandler(sh)
logger.addHandler(fh)

baselog = logging.getLogger('cryptle')
baselog.setLevel(logging.METRIC)
baselog.addHandler(fh)


if __name__ == '__main__':
    logger.debug("Initialising BitstampFeed")
    bs = BitstampFeed()

    logger.debug("Initialising portfolio")
    port = Portfolio(10000)

    logger.debug("Initialising strategies")
    strat = WMAMACDRSIStrat(
            period=120,
            timeframe=3600,
            bband=6.0,
            bband_period=20,
            pair='bchusd',
            portfolio=port,
            message='[MACD]')

    logger.debug("Setting up callbacks")
    bs.onTrade('bchusd', strat.pushTick)

    logger.debug("Reporting...")
    while bs.isConnected():
        logger.report('MACD Equity:    %.2f' % port.equity)
        logger.report('MACD Cash:    %.2f' % port.cash)
        logger.report('MACD Asset:    %s' % str(port.balance))

        time.sleep(120)



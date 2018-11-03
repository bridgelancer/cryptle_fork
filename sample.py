"""Barebones implementation of a Cryptle strategy without using optional Cryptle
subsystems.

The sample is tested with a historical dataset in the main() function by manual
wiring of data source and a mock exchange object. For more a more detailed look
at backtest and deployment in Cryptle, refer to the topic guides in
documentation.
"""

import os
import sys
import logging

import cryptle.logging
from cryptle.strategy import SingleAssetStrategy
from cryptle.exchange import Paper


class MillionDollarStrat(SingleAssetStrategy):
    def setTrade(self):
        self.buy = 0
        self.sell = 0

    def onTrade(self, price, timestamp, volume, action):
        if price < 2580 and not self.hasBalance():
            self.buy += 1
            self.marketBuy(1)

        if price > 2630 and self.hasBalance():
            self.sell += 1
            self.marketSell(1)


def main():
    starting_capital = 10000
    exchange = Paper(starting_capital)
    strat = MillionDollarStrat(exchange, 'bch')
    strat.portfolio.cash = starting_capital
    strat.setTrade()

    # get sample data from the unittest package
    from test import utils
    trades = utils.get_sample_trades()

    for trade in trades:
        price, ts, vol, action = trade
        exchange.updatePrice('bchusd', float(price))
        strat.pushTrade(float(price), int(ts), float(vol), int(action))


if __name__ == '__main__':
    logger = logging.getLogger('cryptle')
    logger.setLevel(logging.DEBUG)
    main()

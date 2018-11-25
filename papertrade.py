from cryptle.datafeed import BitstampFeed
from cryptle.exchange import Paper
from cryptle.backtest import Backtest
from cryptle.strategy import Portfolio
import cryptle.logging

import sys
import logging
from collections import OrderedDict


if __name__ == '__main__':
    exchange = Paper(10000)

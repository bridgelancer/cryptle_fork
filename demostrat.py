from cryptle.strategy import *
from cryptle.loglevel import *
from cryptle.backtest import *
from plotting import *
from ta import *

import logging
import sys
import matplotlib.pyplot as plt

class DemoStrat(Strategy):

    def __init__(s, period=180, wma1_lb=5, wma2_lb=8, **kws):
        # **kws needs to include:
        # - pair
        # - portfolio
        # - exchange

        s.indicators = {}
        s.indicators['vwma'] = ContinuousVWMA(300)
        s.indicators['candle'] = candle = CandleBar(period)
        s.wma1 = WMA(candle, wma1_lb)
        s.wma2 = WMA(candle, wma2_lb)

        s.buy_signal = False
        s.sell_signal = False
        s.entered = False

        # !Important! This line needs to be at the end of __init__
        super().__init__(**kws)


    def handleTick(s, price, timestamp, volume, action):
        if s.vwma > 10000:
            s.buy_signal = True
            s.sell_signal = False
        elif s.vwma < -10000:
            s.buy_signal = False
            s.sell_signal = True


    def execute(s, timestamp):
        if s.buy_signal and s.hasCash and not s.entered:
            s.marketBuy(s.maxBuyAmount)
            s.entered = True
            return

        if s.sell_signal and s.entered:
            s.marketSell(s.maxSellAmount)
            s.entered = False
            return


if __name__ == '__main__':
    dataset = '../../../../data/bitstamp/bch/4.log'
    #pair = 'btcusd'
    #port = Portfolio(10000)
    #exchange = PaperExchange(commission=0.0012)

    #strat = DemoStrat(pair=pair, portfolio=port, exchange=exchange)

    #test = Backtest(exchange)
    #test.readJSON(dataset)
    #test.run(strat.tick)

    strat = DemoStrat()
    backtest_tick(strat, dataset, pair='bchusd')

    plotCandles(
            strat.candle,
            title='Final equity {} Trades:{}'.format(strat.equity, len(strat.trades)),
            trades=strat.trades)
    plt.show()


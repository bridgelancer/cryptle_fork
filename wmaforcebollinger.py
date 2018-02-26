'''@Deprecated'''

from cryptle.strategy import Strategy
from cryptle.loglevel import *

from ta import *

import logging
logger = logging.getLogger('Cryptle')


class WMAForceBollingerStrat(Strategy):

    def __init__(s,
            message='[Force Bollinger]',
            period=180,
            scope1=5,
            scope2=8,
            upper_atr=0.5,
            lower_atr=0.5,
            timeframe=3600,
            bband=3.5,
            bband_period=20,
            vol_multipler=30,
            vwma_lb=40,
            **kws):

        s.indicators = {}

        s.indicators['bar'] = CandleBar(period)
        s.indicators['vwma1'] = ContinuousVWMA(period * 3) # @HARDCODE
        s.indicators['vwma2'] = ContinuousVWMA(period * vwma_lb) # @HARDCODE

        super().__init__(**kws)

        s.ATR_5 = ATR(s.bar, scope1)
        s.WMA_5 = WMA(s.bar, scope1)
        s.WMA_8 = WMA(s.bar, scope2)
        s.sma_20 = SMA(s.bar, bband_period)
        s.bollinger = BollingerBand(s.sma_20, bband_period)

        s.message = message
        s.timelag_required = 15
        s.upper_atr = upper_atr
        s.lower_atr = lower_atr
        s.bband = bband
        s.timeframe = timeframe
        s.vol_multipler = vol_multipler

        s.tradable_window = 0
        s.init_time = 0
        s.dollar_volume_flag = False
        s.bollinger_signal = False
        s.can_sell = False
        s.v_sell = False


    def handleTick(s, price, timestamp, volume, action):

        s.buy_signal = False
        s.sell_signal = False
        s.v_sell_signal = False

        if s.init_time == 0:
            s.init_time = timestamp

        if timestamp < s.init_time + max(s.WMA_8.lookback, 20) * s.bar.period:
            return

        # @ta should not raise RuntimeWarning
        try:
            atr = s.ATR_5.atr

            belowatr = max(s.WMA_5.wma, s.WMA_8.wma) < price - s.lower_atr * atr
            aboveatr = min(s.WMA_5.wma, s.WMA_8.wma) > price + s.upper_atr * atr
        except RuntimeWarning:
            return

        s.uptrend   = s.WMA_5.wma > s.WMA_8.wma
        s.downtrend = s.WMA_5.wma < s.WMA_8.wma

        # @HARDCODE Buy/Sell message
        # @TODO should not trade the first signal if we enter the bollinger_signal with an uptrend?

        # Buy/Sell singal generation
        # Band confirmation
        norm_vol1 = s.vwma1.dollar_volume / s.vwma1.period
        norm_vol2 = s.vwma2.dollar_volume / s.vwma2.period

        # Dollar volume signal # hard code threshold for the moment
        if s.hasBalance and  norm_vol1 > norm_vol2 * s.vol_multipler:
            s.dollar_volume_flag = True
        else:
            s.dollar_volume_flag = False

        if s.bollinger.band > s.bband: # currently snooping 3.5%
            s.bollinger_signal = True
            s.tradable_window = timestamp
        if timestamp > s.tradable_window + s.timeframe: # available at 1h trading window (3600s one hour)
            s.bollinger_signal = False

        if s.hasCash and not s.hasBalance:
            if s.v_sell:
                if s.uptrend or belowatr or aboveatr:
                    return
                elif s.downtrend:
                    s.v_sell = False
            elif belowatr:
                s.buy_signal = True
            else:
                s.prev_crossover_time = None

        elif s.hasBalance:
            if s.dollar_volume_flag and s.vwma1.dollar_volume <= 0:
                s.v_sell_signal = True
                logger.signal("VWMA Indicate sell at: " + str(timestamp))
            elif not s.can_sell and aboveatr:
                s.sell_signal = True
            elif s.can_sell and s.downtrend:
                s.sell_signal = True
            elif not s.can_sell and s.uptrend:
                s.can_sell = True
            elif not s.can_sell and s.downtrend:
                return

        else:
            s.prev_crossover_time = None

    # Can only buy if buy_signal and bollinger_signal both exist
    def execute(s, timestamp):
        if s.hasCash and not s.hasBalance and s.buy_signal and s.bollinger_signal:
            if s.prev_crossover_time is None:
                s.prev_crossover_time = s.timestamp # @Hardcode @Fix logic, do not use timestamp here

            elif s.timestamp - s.prev_crossover_time >= s.timelag_required:
                s.marketBuy(s.maxBuyAmount)

                s.prev_crossover_time = None
                # setting can_sell flag for preventing premature exit
                if s.uptrend:
                    s.can_sell = True
                elif s.downtrend:
                    s.can_sell = False

        # Sell immediately if v_sell signal is present, do not enter the position before next uptrend
        elif s.hasBalance and s.v_sell_signal:
            s.marketSell(s.maxSellAmount)

            s.prev_crossover_time = None
            s.dollar_volume_flag = False

            s.v_sell = True

        elif s.hasBalance and s.sell_signal:

            if s.prev_crossover_time is None:
                s.prev_crossover_time = s.timestamp

            elif s.timestamp - s.prev_crossover_time >= s.timelag_required:

                s.marketSell(s.maxSellAmount)

                s.prev_crossover_time = None
                s.dollar_volume_flag = False


if __name__ == '__main__':
    from cryptle.backtest import *
    from cryptle.plotting import *
    import matplotlib.pyplot as plt

    pair = 'bchusd'
    port = Portfolio(10000)
    exchange = PaperExchange(commission=0.0012)

    strat = WMAForceBollingerStrat(
            pair=pair,
            portfolio=port,
            exchange=exchange,
            period=180,
            scope1=5,
            scope2=8,
            timeframe=3600)

    test = Backtest(exchange)
    test.readJSON('papertrade0114p_bch.log')
    test.run(strat.tick)

    plotCandles(
            strat.bar,
            title='Final equity {} Trades:{}'.format(strat.equity, len(strat.trades)),
            trades=strat.trades)
    plt.show()

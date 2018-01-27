from cryptle.strategy import Strategy, Portfolio
from cryptle.loglevel import *

from ta import *
import logging

logger = logging.getLogger('Cryptle')


class WMAForceBollingerRSIStrat(Strategy):

    def __init__(s,
            message='[WMA Bollinger RSI]',
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
            rsi_la = 14,
            **kws):

        s.indicators = {}

        s.indicators['bar'] = bar = CandleBar(period)
        s.indicators['vwma1'] = ContinuousVWMA(period * 3) # @HARDCODE
        s.indicators['vwma2'] = ContinuousVWMA(period * vwma_lb) # @HARDCODE

        s.ATR_5 = ATR(bar, scope1)
        s.WMA_5 = WMA(bar, scope1)
        s.WMA_8 = WMA(bar, scope2)
        s.sma_20 = SMA(bar, bband_period)
        s.bollinger = BollingerBand(s.sma_20, bband_period)
        s.rsi = RSI(bar, rsi_la)

        s.period = period
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
        s.was_v_sell = False

        s.rsi_sell_flag = False
        s.rsi_downtrend_time = None
        s.rsi_counter = 0
        s.rsi_max = 0
        s.can_rsi = True
        s.prev_sell_time = None
        s.prev_buy_time = None
        s.prev_buy_price = 0
        s.current_atr = None
        s.stop_loss_price = 0


        super().__init__(**kws)

    def generateSignal(s, price, timestamp, volume, action):

        s.buy_signal = False
        s.sell_signal = False
        s.v_sell_signal = False
        s.rsi_bsignal = False
        s.rsi_ssignal = False

        if s.init_time == 0:
            s.init_time = timestamp

        if timestamp < s.init_time + max(s.WMA_8.lookback, 20) * s.bar.period:
            return


        atr = s.ATR_5.atr

        belowatr = max(s.WMA_5.wma, s.WMA_8.wma) < price - s.lower_atr * atr
        aboveatr = min(s.WMA_5.wma, s.WMA_8.wma) > price + s.upper_atr * atr


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

        # RSI signal generation
        if s.rsi.rsi > 50:
            if s.rsi_sell_flag:
                pass
            elif s.rsi.rsi > 80:
                s.rsi_sell_flag = True
                s.rsi_max = max(s.rsi.rsi, s.rsi_max)
            elif s.uptrend and s.can_rsi:
                s.rsi_bsignal = True
                s.rsi_counter = 0   # why need the counter
                s.rsi_downtrend_time = None
            elif s.downtrend and s.can_rsi:
                if s.rsi_downtrend_time is None:
                    s.rsi_downtrend_time = timestamp
                s.rsi_counter = int(timestamp / s.period) - int(s.rsi_downtrend_time/ s.period)
                s.rsi_bsignal = True
                s.rsi_ssignal = False

        # if downtrend, raise RSI, reset if reached the threshold
        if s.rsi.rsi < 50 + s.rsi_counter * (s.period/60):
            s.rsi_ssignal = True
            s.rsi_sell_flag = False
            s.rsi_downtrend_time = None
            s.rsi_counter = 0

        if s.rsi.rsi < s.rsi_max - 20:
            if s.rsi_sell_flag:
                s.rsi_ssignal = True
                s.rsi_bsignal = False
                s.rsi_max = 0

        if not s.can_rsi and s.rsi.rsi < 50:
            s.can_rsi = True



        # Buy sell signal generation
        if s.hasCash and not s.hasBalance:
            if s.was_v_sell:
                if s.uptrend or belowatr or aboveatr:
                    return
                elif s.downtrend:
                    s.was_v_sell = False
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

    # @Regression: Timestamp/Price/unneccesary signals shouldn't be here
    # Execution of signals
    # Can only buy if buy_signal and bollinger_signal both exist
    def execute(s, timestamp):
        if s.hasCash and not s.hasBalance and s.buy_signal and s.bollinger_signal and s.rsi_bsignal:
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

            s.was_v_sell = True


        elif s.hasBalance and s.rsi_sell_flag and s.rsi_ssignal:
            logger.signal("Sell at max - 20:" + str(s.rsi.rsi))
            s.marketSell(s.maxSellAmount, appendTimestamp(s.message, s.timestamp))
            s.prev_crossover_time = None
            s.dollar_volume_flag = False

            s.can_rsi = False


        elif s.hasBalance and s.sell_signal and s.rsi_ssignal:
            logger.signal("Sell at RSI: " + str(s.rsi.rsi))

            if s.prev_crossover_time is None:
                s.prev_crossover_time = s.timestamp

            elif s.timestamp - s.prev_crossover_time >= s.timelag_required:

                s.marketSell(s.maxSellAmount, appendTimestamp(s.message, s.timestamp))

                s.prev_crossover_time = None
                s.dollar_volume_flag = False


from cryptle.backtest import Backtest, PaperExchange
from plotting import *
import matplotlib.pyplot as plt


if __name__ == '__main__':
    pair = 'bchusd'
    port = Portfolio(10000)
    exchange = PaperExchange(commission=0.0012)

    strat = WMAForceBollingerRSIStrat(
            pair=pair,
            portfolio=port,
            exchange=exchange,
            period=180,
            scope1=5,
            scope2=8,
            timeframe=3600)

    test = Backtest(exchange)
    test.readJSON('bch.log')
    test.run(strat.tick)

    plotCandles(
            strat.bar,
            title='Final equity {} Trades:{}'.format(strat.equity, len(strat.trades)),
            trades=strat.trades)
    plt.show()

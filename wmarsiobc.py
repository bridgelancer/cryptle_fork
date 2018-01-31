from cryptle.strategy import Strategy, Portfolio
from cryptle.loglevel import defaultFormatter
from cryptle.utility  import *
from ta import *

import logging
logger = logging.getLogger('Cryptle')


class WMARSIOBCStrat(Strategy):

    def __init__(s,
            message='[RSI OBC]',
            period=180,
            scope1=5,
            scope2=8,
            upper_atr=0.5,
            lower_atr=0.5,
            timeframe=3600,
            bband=3.5,
            bband_period=20,
            vol_multiplier=30,
            vwma_lb=40,
            rsi_lb=14,
            timelag_required=10,
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
        s.rsi = RSI(bar, rsi_lb)

        s.period = period
        s.message = message
        s.timelag_required = timelag_required
        s.upper_atr = upper_atr
        s.lower_atr = lower_atr
        s.bband = bband
        s.timeframe = timeframe
        s.vol_multiplier = vol_multiplier

        s.tradable_window = 0
        s.init_time = 0
        # s.dollar_volume_flag = False
        s.bollinger_signal = False
        s.can_sell = False
        # s.was_v_sell = False

        s.rsi_sell_flag = False
        s.rsi_sell_flag_80 = False
        s.prev_crossover_time = None
        # s.prev_sell_time = None
        s.rsi_bsignal = None
        s.rsi_ssignal = None
        # s.current_atr = None
        s.prev_buy_time = None
        s.prev_buy_price = 0
        s.stop_loss_price = 0
        s.price = 0
        s.buy_signal = None
        s.sell_signal = None
        s.v_sell_signal = None

        super().__init__(**kws)

    def handleTick(s, price, timestamp, volume, action):

        s.price = price

        if s.init_time == 0:
            s.init_time = timestamp

        if timestamp < s.init_time + max(s.WMA_8.lookback, 20) * s.bar.period:
            return

        atr = s.ATR_5.atr

        belowatr = max(s.WMA_5.wma, s.WMA_8.wma) < price - s.lower_atr * atr
        aboveatr = min(s.WMA_5.wma, s.WMA_8.wma) > price + s.upper_atr * atr

        s.uptrend   = s.WMA_5.wma > s.WMA_8.wma
        s.downtrend = s.WMA_5.wma < s.WMA_8.wma

        # @TODO should not trade the first signal if we enter the bollinger_signal with an uptrend?

        # Dollar volume signal # hard code threshold for the moment
        # norm_vol1 = s.vwma1.dollar_volume / s.vwma1.period
        # norm_vol2 = s.vwma2.dollar_volume / s.vwma2.period

        # if s.hasBalance and  norm_vol1 > norm_vol2 * s.vol_multiplier:
        #     s.dollar_volume_flag = True
        # else:
        #     s.dollar_volume_flag = False

        # Band confirmation
        if s.bollinger.band > s.bband: # s.bband = 3.0 by default
            s.bollinger_signal = True
            s.tradable_window = timestamp
        if timestamp > s.tradable_window + s.timeframe: # available at 1h trading window (3600s one hour)
            s.bollinger_signal = False

        # RSI signal generation
        rsi_bsignal = False # local variable
        rsi_ssignal = False # local variable
        rsi_sell_flag = s.rsi_sell_flag
        rsi_sell_flag_80 = s.rsi_sell_flag_80

        if s.rsi.rsi > 50:
            if s.rsi.rsi > 70:
                rsi_bsignal = True
                rsi_ssignal = False
                rsi_sell_flag = True
            elif s.rsi.rsi > 80:
                rsi_bsignal = True
                rsi_ssignal = False
                rsi_sell_flag_80 = True
            else:
                rsi_bsignal = True
                rsi_ssignal = False

        if rsi_sell_flag and s.downtrend:
            rsi_ssignal = True
            rsi_bsignal = False

        if rsi_sell_flag_80 and s.rsi.rsi < 70:
            rsi_ssignal = True
            rsi_bsignal = False

        if s.rsi.rsi < 50:
            rsi_ssignal = True
            rsi_bsignal = False
            rsi_sell_flag = False
            rsi_sell_flag_80 = False

        s.rsi_bsignal = rsi_bsignal
        s.rsi_ssignal = rsi_ssignal
        s.rsi_sell_flag = rsi_sell_flag
        s.rsi_sell_flag_80 = rsi_sell_flag_80

        # Buy sell signal generation
        buy_signal = False
        sell_signal = False
        v_sell_signal = False

        if s.hasCash and not s.hasBalance:
            # if s.was_v_sell:
            #     if s.uptrend or belowatr or aboveatr:
            #         return
            #     elif s.downtrend:
            #         s.was_v_sell = False
            if belowatr:
                buy_signal = True
            else:
                s.prev_crossover_time = None

        elif s.hasBalance:
            # if s.dollar_volume_flag and s.vwma1.dollar_volume <= 0: # Currently no use
            #     v_sell_signal = True
            #     #logger.signal("VWMA Indicate sell at: " + str(timestamp))
            if not s.can_sell and aboveatr:
                sell_signal = True
            elif s.can_sell and s.downtrend:
                sell_signal = True
            elif not s.can_sell and s.uptrend:
                can_sell = True
            elif not s.can_sell and s.downtrend:
                pass

        else:
            s.prev_crossover_time = None

        #Do not allow trade if this tick is still within the same bar with prev_buy_time
        try:
            if int(timestamp/s.period) == int(s.prev_buy_time/ s.period):
                return -1
            # Reset prev_buy_time to none s.t. this won't try after the first admissible tick to stop loss
            elif int(timestamp / s.period) > int(s.prev_buy_time / s.period):
            # if int(timestamp / s.period) > int(s.prev_buy_time / s.period):
                bar_diff = int(timestamp / s.period) - int(s.prev_buy_time / s.period)
                bar_min = min(s.bar.bars[-1 - bar_diff][0], s.bar.bars[-1 - bar_diff][1])
                #stop_loss_price = min(bar_min * .99, bar_min - current_atr)
                s.stop_loss_price = bar_min * .0
                #stop_loss_price = 0

                s.prev_buy_time == None
        except TypeError:
            pass

        s.buy_signal = buy_signal
        s.sell_signal = sell_signal
        s.v_sell_signal = v_sell_signal


    # Signal execution
    def execute(s, timestamp):
        if s.hasCash and not s.hasBalance and s.buy_signal and s.bollinger_signal and s.rsi_bsignal:
            if s.prev_crossover_time is None:
                s.prev_crossover_time = timestamp # @Hardcode @Fix logic, do not use timestamp here

            elif timestamp - s.prev_crossover_time >= s.timelag_required:
                s.marketBuy(s.maxBuyAmount)

                s.prev_crossover_time = None
                s.prev_buy_time = timestamp
                s.prev_buy_price = s.price
                # setting can_sell flag for preventing premature exit
                if s.uptrend:
                    s.can_sell = True
                elif s.downtrend:
                    s.can_sell = False

        #Sell immediately if v_sell signal is present, do not enter the position before next uptrend
        #Currently commented out because of lack of valid snooping mechanism
        # elif s.hasBalance and s.v_sell_signal:
        #     s.marketSell(s.maxSellAmount)

        #     s.prev_crossover_time = None
        #     s.dollar_volume_flag = False

        #     s.was_v_sell = True

        # elif s.hasBalance and s.rsi_sell_flag and s.rsi_ssignal:
        #     #logger.signal("Sell at max - 20:" + str(s.rsi.rsi))
        #     s.marketSell(s.maxSellAmount, appendTimestamp(s.message, timestamp))
        #     s.prev_crossover_time = None
        #     s.dollar_volume_flag = False
        elif s.hasBalance and s.price < s.stop_loss_price and int(timestamp / s.period) > int(s.prev_buy_time / s.period):
            s.marketSell(s.maxSellAmount, appendTimestamp(s.message, timestamp))

            s.prev_crossover_time = None
            s.dollar_volume_flag = False
            s.prev_buy_price = 0
            s.prev_buy_time = None

            # now setting no stop loss for the moment

        elif s.hasBalance and s.rsi_ssignal and s.rsi_sell_flag:
            s.marketSell(s.maxSellAmount, appendTimestamp(s.message, timestamp))

            s.prev_crossover_time = None
            s.dollar_volume_flag = False
            s.prev_buy_price = 0
            s.prev_buy_time = None
            s.rsi_sell_flag = False
            s.rsi_sell_flag_80 = False

        elif s.hasBalance and s.rsi_ssignal and s.rsi_sell_flag_80:
            s.marketSell(s.maxSellAmount, appendTimestamp(s.message, timestamp))

            s.prev_crossover_time = None
            s.dollar_volume_flag = False
            s.prev_buy_price = 0
            s.prev_buy_time = None
            s.rsi_sell_flag = False
            s.rsi_sell_flag_80 = False

        elif s.hasBalance and s.sell_signal and s.rsi_ssignal:
            #logger.signal("Sell at RSI: " + str(s.rsi.rsi))

            if s.prev_crossover_time is None:
                s.prev_crossover_time = timestamp

            elif timestamp - s.prev_crossover_time >= s.timelag_required:
                s.marketSell(s.maxSellAmount, appendTimestamp(s.message, timestamp))

                s.prev_crossover_time = None
                s.dollar_volume_flag = False
                s.prev_buy_price = 0
                s.prev_buy_time = None


if __name__ == '__main__':
    from cryptle.backtest import backtest_tick, Backtest, PaperExchange
    from cryptle.plotting import plot
    import matplotlib.pyplot as plt

    formatter = defaultFormatter()

    fh = logging.FileHandler('rsiobc.log', mode='w')
    fh.setLevel(logging.INDEX)
    fh.setFormatter(formatter)

    sh = logging.StreamHandler()
    sh.setLevel(logging.REPORT)
    sh.setFormatter(formatter)

    logger.setLevel(logging.INDEX)
    logger.addHandler(sh)
    logger.addHandler(fh)

    base_logger = logging.getLogger('cryptle.strategy')
    base_logger.setLevel(logging.DEBUG)
    base_logger.addHandler(fh)

    # Handler for recording indicators
    equity = []

    def record_indicators(strat):
        global equity
        equity.append((strat.last_timestamp, strat.equity))


    dataset = 'data/bch_correct.log'

    pair = 'bchusd'
    port = Portfolio(10000)
    exchange = PaperExchange(commission=0.0012, slippage=0)

    strat = WMARSIOBCStrat(
        period=120,
        timeframe=3600,
        bband=6,
        bband_period=20,
        vwma_lb=40,
        rsi_lb=14,
        timelag_required=0,
        pair=pair,
        portfolio=port,
        exchange=exchange,
        equity_at_risk=1)

    backtest_tick(strat, dataset, exchange=exchange) #, callback=record_indicators)

    logger.report('Period: {} BBand: {} BPeriod: {}'
            .format(strat.period, strat.bband, strat.bollinger.lookback))

    logger.report('RSI Equity:    %.2f' % port.equity)
    logger.report('RSI Cash:    %.2f' % port.cash)
    logger.report('RSI Asset:    %s' % str(port.balance))
    logger.report('Number of trades:  %d' % len(strat.trades))
    logger.report('Number of candles: %d' % len(strat.bar))

    equity = [[x[0] for x in equity], [x[1] for x in equity]]

    plt.plot(equity[0], equity[1])
    plt.show()

    plot(
        strat.bar,
        title='Final equity: ${} Trades: {}'.format(strat.equity, len(strat.trades)),
        trades=strat.trades,
        indicators=[[equity]])
    plt.show()
    # fig.savefig('some_plot.png', dpi=1000)

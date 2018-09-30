from cryptle.strategy import Strategy, Portfolio
from cryptle.loglevel import *

from ta import *

import logging
logger = logging.getLogger('Strategy')


class MACDSNBStrat(Strategy):

    def __init__(s,
            message='[MACD RSI]',
            period=180,
            scope1=5,
            scope2=8,
            macd_scope=4,
            upper_atr=0.5,
            lower_atr=0.5,
            timeframe=3600,
            bband=3.5,
            bband_period=20,
            vol_multipler=30,
            vwma_lb=40,
            rsi_la=14,
            **kws):

        s.indicators = {}

        s.indicators['bar'] = bar = CandleBar(period)
        s.indicators['vwma1'] = ContinuousVWMA(period * 3) # @HARDCODE
        s.indicators['vwma2'] = ContinuousVWMA(period * vwma_lb) # @HARDCODE

        # Initialize appropriate TAs
        s.ATR_5 = ATR(bar, scope1)
        s.WMA_5 = WMA(bar, scope1)
        s.WMA_8 = WMA(bar, scope2)
        s.macd = MACD_WMA(s.WMA_5, s.WMA_8, macd_scope)
        s.sma_20 = SMA(bar, bband_period)
        s.bollinger = BollingerBand(s.sma_20, bband_period)
        s.snb = SNB(s.bollinger , 10)
        s.rsi = RSI(bar, rsi_la)

        # Initialize key parameters of the strategy
        s.period = period
        s.message = message
        s.timelag_required = 10 # @HARDCODE
        s.upper_atr = upper_atr
        s.lower_atr = lower_atr
        s.bband = bband
        s.timeframe = timeframe
        s.vol_multipler = vol_multipler

        # Initialize class storage of local instances of signals for execution
        s.tradable_window = 0
        s.init_time = 0
        # s.dollar_volume_flag = False
        s.bollinger_signal = False
        s.rsi_bsignal = None
        s.rsi_ssignal = None
        # s.was_v_sell = False

        # Initialize flags and states related to the processing of incoming tick / bar
        s.rsi_sell_flag = False
        s.rsi_sell_flag_80 = False
        s.prev_crossover_time = None
        # s.prev_sell_time = None
        # s.current_atr = None
        s.prev_buy_time = None
        s.prev_buy_price = 0
        s.stop_loss_time = None
        s.stop_loss_price = 0
        s.price = 0

        super().__init__(**kws)

    # Bar version of macdrsi strategy
    def handleCandle(s, op, cl, hi, lo, ts, vol):
        s.price = cl

        # Track initialization time
        if s.init_time == 0:
            s.init_time = ts
        # Terminate all subsequent processes if there is not enough bars collected
        if ts < s.init_time + max(s.WMA_8.lookback, 20) * s.bar.period:
            return

        # Band confirmation
        if s.bollinger.band > s.bband:
            s.bollinger_signal = True
            s.tradable_window = timestamp
        if timestamp > s.tradable_window + s.timeframe: # available at 1h trading window (3600s one hour)
            s.bollinger_signal = False

        # MACD singal generation
        s.macd_signal = False

        if s.macd.wma3 < s.macd.wma1.wma - s.macd.wma2.wma :
            s.macd_signal = True
        else:
            s.macd_signal = False

        # RSI signal generation
        rsi_bsignal = False # local variable
        rsi_ssignal = False # local variable

        if s.rsi.rsi > 50:
            if s.rsi.rsi > 70:
                rsi_bsignal = True
                rsi_ssignal = False
                s.rsi_sell_flag = True
            elif s.rsi.rsi > 80:
                rsi_bsignal = True
                rsi_ssignal = False
                s.rsi_sell_flag_80 = True
            else:
                rsi_bsignal = True
                rsi_ssignal = False

        if s.rsi_sell_flag and s.downtrend:
            rsi_ssignal = True
            rsi_bsignal = False

        if s.rsi_sell_flag_80 and s.rsi.rsi < 70:
            rsi_ssignal = True
            rsi_bsignal = False

        if s.rsi.rsi < 50:
            rsi_ssignal = True
            rsi_bsignal = False
            s.rsi_sell_flag = False
            s.rsi_sell_flag_80 = False

        s.rsi_bsignal = rsi_bsignal
        s.rsi_ssignal = rsi_ssignal

        #Do not allow trade if this tick is still within the same bar with prev_buy_time
        try:
            if int(ts / s.period) > int(s.prev_buy_time / s.period):
            # if int(timestamp / s.period) > int(s.prev_buy_time / s.period):
                bar_diff = int(ts / s.period) - int(s.prev_buy_time / s.period)
                bar_min = min(s.bar.bars[-1 - bar_diff][0], s.bar.bars[-1 - bar_diff][1])
                #stop_loss_price = min(bar_min * .99, bar_min - current_atr)
                s.stop_loss_price = bar_min * .00
                #stop_loss_price = 0

                s.prev_buy_time == None
        except TypeError:
            pass

    def handleTick(s, price, timestamp, volume, action):

        s.price = price
        # Track initialization time
        if s.init_time == 0:
            s.init_time = timestamp
        # Terminate all subsequent processes if there is not enough bars collected
        if timestamp < s.init_time + max(s.WMA_8.lookback, 20) * s.bar.period:
            return
        # Miscellaneous indicators
        atr = s.ATR_5.atr
        belowatr = max(s.WMA_5.wma, s.WMA_8.wma) < price - s.lower_atr * atr
        s.uptrend   = s.WMA_5.wma > s.WMA_8.wma
        s.downtrend = s.WMA_5.wma < s.WMA_8.wma

        # @TODO should not trade the first signal if we enter the bollinger_signal with an uptrend?

        # Dollar volume signal # hard code threshold for the moment
        # norm_vol1 = s.vwma1.dollar_volume / s.vwma1.period
        # norm_vol2 = s.vwma2.dollar_volume / s.vwma2.period

        # if s.hasBalance and  norm_vol1 > norm_vol2 * s.vol_multipler:
        #     s.dollar_volume_flag = True
        # else:
        #     s.dollar_volume_flag = False

        # Band confirmation

        # Band confirmation - solve logic bug
        if timestamp > s.tradable_window + s.timeframe: # available at 1h trading window (3600s one hour)
            s.bollinger_signal = False

        if s.snb.sma[-1] * 1.25 < s.bollinger.band and s.bollinger.band > 3:
            s.bollinger_signal = True

        if s.bollinger.band > s.bband:
            s.bollinger_signal = True
            s.tradable_window = timestamp

        # MACD singal generation
        if s.macd.wma3 < s.macd.wma1.wma - s.macd.wma2.wma :
            s.macd_signal = True
        else:
            s.macd_signal = False

        # RSI signal generation
        rsi_bsignal = False # local variable
        rsi_ssignal = False # local variable

        if s.rsi.rsi > 50:
            if s.rsi.rsi > 70:
                if not s.rsi_sell_flag:
                    logger.metric('RSI Over 70')
                rsi_bsignal = True
                rsi_ssignal = False
                s.rsi_sell_flag = True
            elif s.rsi.rsi > 80:
                if not s.rsi_sell_flag_80:
                    logger.metric('RSI Over 80')
                rsi_bsignal = True
                rsi_ssignal = False
                s.rsi_sell_flag_80 = True
            else:
                rsi_bsignal = True
                rsi_ssignal = False

        if s.rsi_sell_flag and s.downtrend:
            rsi_ssignal = True
            rsi_bsignal = False

        if s.rsi_sell_flag_80 and s.rsi.rsi < 70:
            rsi_ssignal = True
            rsi_bsignal = False

        if s.rsi.rsi < 50:
            rsi_ssignal = True
            rsi_bsignal = False
            s.rsi_sell_flag = False
            s.rsi_sell_flag_80 = False

        s.rsi_bsignal = rsi_bsignal
        s.rsi_ssignal = rsi_ssignal

        # Set prev_crossover_time = None if not belowatr
        if s.hasCash and not s.hasBalance:
            # if s.was_v_sell:
            #     if s.uptrend or belowatr or aboveatr:
            #         return
            #     elif s.downtrend:
            #         s.was_v_sell = False
            if belowatr:
                pass
            else:
                s.prev_crossover_time = None

        elif s.hasBalance:
            # if s.dollar_volume_flag and s.vwma1.dollar_volume <= 0: # Currently no use
            #     v_sell_signal = True
            #     #logger.signal("VWMA Indicate sell at: " + str(timestamp))
                pass

        else:
            s.prev_crossover_time = None

        #Stop loss module - do not allow buy/sell within the same bar - should not be setting stop loss
        try:
            if int(timestamp/s.period) == int(s.prev_buy_time/ s.period):
                return -1
            # Reset prev_buy_time to none s.t. this won't try after the first admissible tick to stop loss
            elif int(timestamp / s.period) > int(s.prev_buy_time / s.period):
            # if int(timestamp / s.period) > int(s.prev_buy_time / s.period):
                bar_diff = int(timestamp / s.period) - int(s.prev_buy_time / s.period)
                bar_min = min(s.bar.bars[-1 - bar_diff][0], s.bar.bars[-1 - bar_diff][1])
                #stop_loss_price = min(bar_min * .99, bar_min - current_atr)
                s.stop_loss_price = bar_min * .00
                #stop_loss_price = 0

                s.prev_buy_time == None
        except TypeError:
            pass


    # @Regression: Timestamp/Price/unneccesary signals shouldn't be here
    # Execution of signals
    # Can only buy if buy_signal and bollinger_signal both exist

    # If the strategy works with candleBar, there should be no prev_crossover_time
    def execute(s, timestamp):
        if s.hasCash and not s.hasBalance and s.rsi_bsignal and s.bollinger_signal and s.macd_signal:
            if s.prev_crossover_time is None:
                s.prev_crossover_time = timestamp # @Hardcode @Fix logic, do not use timestamp here

            elif timestamp - s.prev_crossover_time >= s.timelag_required:
                s.marketBuy(s.maxBuyAmount)

                s.prev_crossover_time = None
                s.prev_buy_time = timestamp
                s.prev_buy_price = s.price

        #Sell immediately if v_sell signal is present, do not enter the position before next uptrend
        #Currently commented out because of lack of valid snooping mechanism
        # elif s.hasBalance and s.v_sell_signal:
        #     s.marketSell(s.maxSellAmount)

        #     s.prev_crossover_time = None
        #     s.dollar_volume_flag = False

        #     s.was_v_sell = True

        elif s.hasBalance and s.price < s.stop_loss_price:
            s.marketSell(s.maxSellAmount)
            logger.signal('Sell: Triggered stoploss')

            s.prev_crossover_time = None
            s.dollar_volume_flag = False
            s.prev_buy_price = 0
            s.prev_buy_time = None

            s.stop_loss_time = timestamp
            s.stop_loss_flag = True
            s.stop_loss_price = 0

            # now setting no stop loss for the moment

        elif s.hasBalance and s.rsi_ssignal and s.rsi_sell_flag:
            s.marketSell(s.maxSellAmount)
            logger.signal('Sell: Over 70 RSI')

            s.prev_crossover_time = None
            s.dollar_volume_flag = False
            s.prev_buy_price = 0
            s.prev_buy_time = None
            s.stop_loss_price = 0
            s.rsi_sell_flag = False
            s.rsi_sell_flag_80 = False

        elif s.hasBalance and s.rsi_ssignal and s.rsi_sell_flag_80:
            s.marketSell(s.maxSellAmount)
            logger.signal('Sell: Over 80 RSI')

            s.prev_crossover_time = None
            s.dollar_volume_flag = False
            s.prev_buy_price = 0
            s.prev_buy_time = None
            s.stop_loss_price = 0
            s.rsi_sell_flag = False
            s.rsi_sell_flag_80 = False

        elif s.hasBalance and s.rsi_ssignal and not s.macd_signal:

            s.marketSell(s.maxSellAmount)
            logger.signal('Sell: Normal RSI + MACD')

            s.prev_crossover_time = None
            s.dollar_volume_flag = False
            s.prev_buy_price = 0
            s.prev_buy_time = None
            s.stop_loss_price = 0


if __name__ == '__main__':
    from cryptle.backtest import backtest_tick, Backtest, PaperExchange
    from cryptle.plotting import *
    import matplotlib.pyplot as plt

    formatter = defaultFormatter()
    fh = logging.FileHandler('macd_rsi.log', mode = 'w')
    fh.setLevel(logging.TICK)
    fh.setFormatter(formatter)

    sh = logging.StreamHandler()
    sh.setLevel(logging.REPORT)
    sh.setFormatter(formatter)

    logger.addHandler(sh)
    logger.addHandler(fh)
    logger.setLevel(logging.DEBUG)

    base_logger = logging.getLogger('cryptle.strategy')
    base_logger.setLevel(logging.DEBUG)
    base_logger.addHandler(fh)

    vwma1 = []
    vwma2 = []
    wma5 = []
    wma8 = []
    equity = []
    bband = []
    snb = []
    snb_ma = []
    upperband = []
    lowerband = []
    rsi = []
    macd_diff = []
    macd_signal = []

    def record_indicators(strat):
        global vwma1
        global vwma2
        global wma5
        global wma8
        global equity
        global bband
        global snb
        global snb_ma
        global sharpe_ratio
        global rsi

        vwma1.append((strat.last_timestamp, strat.vwma1.dollar_volume / strat.vwma1.period))
        vwma2.append((strat.last_timestamp, strat.vwma2.dollar_volume / strat.vwma2.period))
        equity.append((strat.last_timestamp, strat.equity))

        if len(strat.bar) > 10:
            wma5.append((strat.last_timestamp, strat.WMA_5.wma))
            wma8.append((strat.last_timestamp, strat.WMA_8.wma))
        if len(strat.bar) > strat.bollinger.lookback:
            bband.append((strat.last_timestamp, strat.bollinger.band))
            upperband.append((strat.last_timestamp, strat.bollinger.upperband))
            lowerband.append((strat.last_timestamp, strat.bollinger.lowerband))
            rsi.append((strat.last_timestamp, strat.rsi.rsi))
            macd_diff.append((strat.last_timestamp, strat.macd.wma1.wma - strat.macd.wma2.wma))
            macd_signal.append((strat.last_timestamp, strat.macd.wma3))

        if len(strat.bar) > 100:
            snb_ma.append((strat.last_timestamp, strat.snb.sma[-1]))



    dataset = 'xrp.log'

    pair = 'xrpusd'
    port = Portfolio(10000)
    exchange = PaperExchange(commission=0.0012, slippage=0)

    strat = MACDSNBStrat(
        pair=pair,
        portfolio=port,
        exchange=exchange,
        period=60,
        timeframe=3600,
        scope1=8,
        scope2=12,
        macd_scope=6,
        bband=6.0,
        bband_period=20)

    # Can use this too
    backtest_tick(strat, dataset, exchange=exchange, callback=record_indicators)

    #test = Backtest(exchange)
    #test.readJSON(dataset)
    #test.run(strat, record_indicators)

    logger.report('MACD Equity:    %.2f' % port.equity)
    logger.report('MACD Cash:    %.2f' % port.cash)
    logger.report('MACD Asset:    %s' % str(port.balance))
    logger.report('Number of trades:  %d' % len(strat.trades))
    logger.report('Number of candles: %d' % len(strat.bar))
    def calculateSP(equity):
        equity_list = []
        returns_list = []
        equity_new = [x for x in equity]
        equity_old = [x for x in equity]
        equity_old.pop() # removed final tick
        equity_new.pop(0) # removed initial tick

        equity_list = filter(lambda tick: int(tick[1][0] / strat.period) > int(tick[0][0] / strat.period) , zip(equity_old, equity_new))

        equity_list = [x[1] for x in equity_list]
        ts, eq = zip(*equity_list)

        for i, item in enumerate(eq):
            try:
                returns = eq[i + int(24*60*60 / strat.period)] / item #Calculate daily return
                returns_list.append(returns)
            except IndexError:
                pass

        returns_list = returns_list[0::int(24*60*60 / strat.period)]
        print (returns_list)

        mean_return = sum(returns_list) / len(returns_list)
        print ("Mean daily return: {}%".format((mean_return - 1)*100))

        mean_square = list(map(lambda y: ((y - mean_return)) ** 2, returns_list))
        stdev_return = (sum(mean_square) / len(returns_list)) ** 0.5
        print ("Standard deviation of total return: {}%".format(stdev_return * 100))

        sharpe_ratio = ((eq[-1] / 10000) - 1) / stdev_return

        print("Sharpe ratio (daily): {}".format(sharpe_ratio))

    # calculateSP(equity)
    vwma1 = [[x[0] for x in vwma1], [x[1] for x in vwma1]]
    vwma2 = [[x[0] for x in vwma2], [x[1] for x in vwma2]]
    wma5 = [[x[0] for x in wma5], [x[1] for x in wma5]]
    wma8 = [[x[0] for x in wma8], [x[1] for x in wma8]]
    upperband = [[x[0] for x in upperband], [x[1] for x in upperband]]
    lowerband = [[x[0] for x in lowerband], [x[1] for x in lowerband]]
    equity = [[x[0] for x in equity], [x[1] for x in equity]]
    bband = [[x[0] for x in bband], [x[1] for x in bband]]
    snb_ma = [[x[0] for x in snb_ma], [x[1] for x in snb_ma]]
    rsi = [[x[0] for x in rsi], [x[1] for x in rsi]]
    macd_diff = [[x[0] for x in macd_diff], [x[1] for x in macd_diff]]
    macd_signal = [[x[0] for x in macd_signal], [x[1] for x in macd_signal]]

    plot(
        strat.bar,
        title='Final equity: ${} Trades: {}'.format(strat.equity, len(strat.trades)),
        trades=strat.trades,
        signals=[wma5, wma8],
        indicators=[[bband, snb_ma], [equity], [macd_diff, macd_signal]])

    plt.show()
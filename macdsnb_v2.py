from cryptle.strategy import Strategy
from cryptle.loglevel import *
from cryptle.utility  import *
from metric.candle import *
from metric.generic import *

import logging
logger = logging.getLogger('Strategy')

class SNBStrat(Strategy):

    def __init__(s,
            message='',
            period=120,
            scope1=5,
            scope2=8,
            macd_scope=4,
            bband=6.0,
            bband_period=20,
            boll_window=3600,
            snb_period=10,
            snb_factor=1.25,
            snb_boll=3,
            rsi_period=14,
            timelag=10,
            upper_atr=0.5,
            lower_atr=0.5,
            **kws):

        # Set meta info
        s.message = message

        # Initialize strategy parameters
        s.period = period
        s.upper_atr = upper_atr
        s.lower_atr = lower_atr
        s.timelag = timelag
        s.boll_window = boll_window
        s.bband = bband
        s.snb_factor = snb_factor
        s.snb_boll = snb_boll

        # Initialize metrics
        s.indicators = {}
        s.indicators['bar'] = bar = CandleBar(period)
        super().__init__(**kws)

        s.atr = ATR(bar, scope1)
        s.wma1 = WMA(bar, scope1)
        s.wma2 = WMA(bar, scope2)
        s.macd = MACD(s.wma1, s.wma2, macd_scope)
        s.sma = SMA(bar, bband_period)
        s.boll = BollingerBand(s.sma, bband_period)
        s.snb = MABollinger(s.boll, snb_period)
        s.rsi = RSI(bar, rsi_period)

        # Initialize flags and states
        s.init_time = 0
        s.init_bar = max(scope1, scope2, macd_scope, bband_period, snb_period, rsi_period)
        s.tradable_window = 0
        s.bollinger_signal = False
        s.rsi_sell_flag = False
        s.rsi_sell_flag_80 = False
        s.rsi_signal = None
        s.prev_crossover_time = None


    def handleTick(s, price, timestamp, volume, action):
        if not s.doneInit(timestamp):
            return -1

        s.signifyATR(price, timestamp)
        s.signifyBoll(timestamp)
        s.signifyMACD()
        s.signifyRSI()


    def doneInit(s, timestamp):
        if s.init_time == 0:
            s.init_time = timestamp
        return timestamp > s.init_time + s.init_bar * s.bar.period


    def signifyATR(s, price, timestamp):
        s.belowatr = max(s.wma1, s.wma2) < price - s.lower_atr * s.atr
        s.downtrend = s.wma1 < s.wma2
        s.atr_signal = False

        if not s.belowatr:
            s.prev_crossover_time = None
        else:
            s.prev_crossover_time = s.prev_crossover_time or timestamp
            if timestamp - s.prev_crossover_time >= s.timelag:
                s.atr_signal = True


    def signifyBoll(s, timestamp):
        if s.boll > s.bband:
            if not s.bollinger_signal:
                logger.metric('Bollinger window opened')
            s.bollinger_signal = True
            s.tradable_window = timestamp
        elif s.snb * s.snb_factor < s.boll and s.boll > s.snb_boll:
            if not s.bollinger_signal:
                logger.metric('Bollinger window opened with snb')
            s.bollinger_signal = True
            s.tradable_window = timestamp
        elif timestamp > s.tradable_window + s.boll_window:
            if s.bollinger_signal:
                logger.metric('Bollinger window closed')
            s.bollinger_signal = False


    def signifyMACD(s):
        s.macd_signal = s.macd < 0


    def signifyRSI(s):
        if s.rsi > 80:
            if not s.rsi_sell_flag_80:
                logger.metric('RSI over 80')
            s.rsi_sell_flag_80 = True

        elif s.rsi > 70:
            if not s.rsi_sell_flag:
                logger.metric('RSI over 70')
            s.rsi_sell_flag = True

        elif s.rsi > 50:
            logger.metric('RSI over 50')
            s.rsi_signal = True

        if s.rsi_sell_flag_80 and s.rsi < 70:
            s.rsi_signal = False

        elif s.rsi_sell_flag and s.downtrend:
            s.rsi_signal = False

        elif s.rsi < 50:
            s.rsi_signal = False


    def execute(s, timestamp):
        if (
                s.hasCash
                and not s.hasBalance
                and s.rsi_signal
                and s.bollinger_signal
                and s.macd_signal
                and s.atr_signal
           ):
            s.marketBuy(s.maxBuyAmount)
            s.reset_params()

        elif s.hasBalance and not s.rsi_signal and s.rsi_sell_flag:
            s.marketSell(s.maxSellAmount)
            s.reset_params()
            logger.signal('Sell: Over 70 RSI')

        elif s.hasBalance and not s.rsi_signal and s.rsi_sell_flag_80:
            s.marketSell(s.maxSellAmount)
            s.reset_params()
            logger.signal('Sell: Over 80 RSI')

        elif s.hasBalance and not s.rsi_signal and not s.macd_signal:
            s.marketSell(s.maxSellAmount)
            s.reset_params()
            logger.signal('Sell: RSI + MACD')


    def reset_params(s):
        s.prev_crossover_time = None
        s.rsi_sell_flag = False
        s.rsi_sell_flag_80 = False


if __name__ == '__main__':
    from cryptle.backtest import backtest_tick, Backtest, PaperExchange
    from cryptle.strategy import Portfolio
    from cryptle.plotting import *

    formatter = defaultFormatter(notimestamp=True)

    fh = logging.FileHandler('snb.log', mode = 'w')
    fh.setLevel(logging.TICK)
    fh.setFormatter(formatter)

    sh = logging.StreamHandler()
    sh.setLevel(logging.REPORT)
    sh.setFormatter(formatter)

    logger.addHandler(sh)
    logger.addHandler(fh)
    logger.setLevel(logging.METRIC)

    base_logger = logging.getLogger('cryptle.strategy')
    base_logger.setLevel(logging.METRIC)
    base_logger.addHandler(fh)

    equity = [[], []]
    def record_indicators(strat):
        global equity
        equity[0].append(strat.last_timestamp)
        equity[1].append(strat.equity)

    dataset = 'bch.log'

    pair = 'bchusd'
    port = Portfolio(10000)
    exchange = PaperExchange(commission=0.0012, slippage=0)

    strat = SNBStrat(
        message='[MACD SNB]',
        period=120,
        scope1=5,
        scope2=8,
        macd_scope=4,
        bband=6.0,
        bband_period=20,
        boll_window=3600,
        snb_period=10,
        snb_factor=1.25,
        rsi_period=14,
        pair=pair,
        portfolio=port,
        exchange=exchange)

    backtest_tick(strat, dataset, exchange=exchange) #, callback=record_indicators)

    logger.report('Cash:    %.2f' % port.cash)
    logger.report('Asset:    %s' % str(port.balance))
    logger.report('No. of trades:  %d' % len(strat.trades))
    logger.report('No. of candles:  %d' % len(strat.bar))

    #plot(
    #    strat.bar,
    #    title='Final equity: ${} Trades: {}'.format(strat.equity, len(strat.trades)),
    #    trades=strat.trades)

    #plt.show()

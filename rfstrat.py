from cryptle.strategy import *
from ta import *

logger = logging.getLogger('Cryptle')

class RFStrat(Strategy):

    def __init__(s, message='[RF]', period=60, scope1=5, scope2=8, **kws):
        s.indicators['five_min'] = ContinuousVWMA(period * scope1)
        s.indicators['eight_min'] = ContinuousVWMA(period * scope2)

        super().__init__(**kws)

        s.message = message
        s.cross_lag = 5
        s.last_cross_time = 2147483648
        s.last_tick_price = 2147483648
        s.last_sell_time = 0
        s.last_dir = None       # 1 is up, 0 is down


    def generateSignal(s, price, timestamp, volume, action):

        up = s.five_min > s.eight_min
        down = s.five_min < s.eight_min

        if s.last_dir is None:
            s.last_dir = 1 if up else 0

        if up and s.last_dir == 0:
            logger.debug('RF identified upcross')
            s.last_cross_time = timestamp
        elif down and s.last_dir == 1:
            logger.debug('RF identified downcross')
            s.last_cross_time = timestamp

        confirm_cross = timestamp >= s.last_cross_time + s.cross_lag

        if up and confirm_cross:
            s.down_signal = False
        elif up and confirm_cross:
            s.down_signal = True

        s.has_recent_rise = price >= 1.0025 * s.last_tick_price
        s.has_recent_sell = timestamp <= 120 + s.last_sell_time

        s.last_tick_price = price


    def execute(s, timestamp):
        if s.has_recent_rise and not s.has_recent_sell and s.hasCash and not s.hasBalance:
            s.marketBuy(s.maxBuyAmount)

        elif s.down_signal and s.hasBalance:
            s.marketSell(s.maxSellAmount)
            s.last_sell_time = timestamp


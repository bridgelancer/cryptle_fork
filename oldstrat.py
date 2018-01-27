from cryptle.strategy import *
from ta import *

class OldStrat(Strategy):
    '''Golden cross strategy using basic VWMA

    @Deprecated
    The original implementation used two continuous windows of VWMA which did
    not take buy/sell into account. That indicator has since been replacecd by
    ContinuousVWMA which takes assigns negative sign to sell trades.
    '''

    def __init__(s, timelag_required=15, **kws):

        s.indicators = {}
        s.indicators['five_min'] = ContinuousVWMA(300)
        s.indicators['eight_min'] = ContinuousVWMA(480)

        super().__init__(**kws)

        s.timelag_required = timelag_required
        s.last_cross_time = 2147483648
        s.last_sell_time = 0
        s.last_dir = None       # 1 is up, 0 is down
        s.up_signal = s.down_signal = False


    def generateSignal(s, price, timestamp, volume, action):

        up = s.five_min > s.eight_min
        down = s.five_min < s.eight_min

        if s.last_dir is None:
            s.last_dir = 1 if up else 0

        if up and s.last_dir == 0:
            s.last_cross_time = timestamp
            return
        elif down and s.last_dir == 1:
            s.last_cross_time = timestamp
            return

        confirm_cross = timestamp >= s.timelag_required + s.last_cross_time

        if up and confirm_cross:
            s.up_signal = True
            s.down_signal = False
        elif up and confirm_cross:
            s.up_signal = False
            s.down_signal = True


    def execute(s, timestamp):
        # @Hardcode Volume of buy/sell
        # @Hardcode Buy timelag
        if s.hasCash and not s.hasBalance and s.up_signal:
            if timestamp >= 120 + s.last_sell_time:
                s.marketbuy(1, message='[Old strat]')

        elif s.hasBalance and s.down_signal:
            s.marketSell(1, message='[Old strat]')
            s.last_sell = timestamp

        s.up_signal = False
        s.down_signal = False


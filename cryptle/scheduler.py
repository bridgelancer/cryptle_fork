import logging
from collections import OrderedDict

from cryptle.event import source, on, Bus
from cryptle.rule import Rule
from collections import OrderedDict


logger = logging.getLogger(__name__)


class Scheduler:
    """ Scheduler class keeps record of the Strategy class's state information.

    A setup tuple would be passed during the construction of the Scheduler. This would
    inialize all the Rules that would be subsequently maintained by the Scheduler and
    also via the interactions between Rules where necessary.

    Args
    ---
    setup: tuple
        The tuple of tuples held by the Strategy

    It is also responsible for controlling the execution of logical tests at desired
    time and frequency as time elapsed. This is achieved by various onEvent functions.
    These functions are responsible for listening to system-generated events via the
    evnet Bus and refreshes the logic_status at suitable time point.

    """

    def __init__(self, *setup):
        self.rules = list(map(Rule, *setup))

        # bar-related states that should be sourced from aggregator
        self.bars = []
        self.open_price = None  # if last bar open price is required, reference to this
        self.close_price = (
            None
        )  # if last bar close price is required, reference to this
        self.num_bars = 0
        self.new_open = False
        self.new_close = False
        # tick-related states that should be sourced from feed
        self.current_price = None
        self.current_time = None
        # trade-related states that should be sourced from OrderBook (or equivalent)
        self.buy_count = 0
        self.sell_count = 0
        self.lookup_check = {'open': self.new_open, 'close': self.new_close, '': True}

        for rule in self.rules:
            rule.initialize()

    # tick should be agnostic to source of origin, but should take predefined format
    @on('tick')
    def onTrade(self, tick):
        # ***this sequence matters a lot***

        # logger.debug('Scheduler received tick: {}', tick)

        if self.current_price is not None:
            self.handleCheck(tick)
        self.new_open = False
        self.new_close = False
        self.current_price = tick[0]
        self.current_time = tick[1]

        self.updateLookUp()

    # separate interface from implementation details
    @on('aggregator:new_open')
    def onOpen(self, price):
        self.new_open = True
        self.open_price = price
        self.updateLookUp()

    # separate interface from implementation details
    @on('aggregator:new_close')
    def onClose(self, price):
        self.close_price = price
        self.new_close = True
        self.updateLookUp()

    def updateLookUp(self):
        self.lookup_check = {'open': self.new_open, 'close': self.new_close, '': True}

    @on('buy')  # 'buy', 'sell' events are not integrated for the moment
    def onBuy(self):
        self.buy_count += 1

    @on('sell')  # 'buy', 'sell' events are not integrated for the moment
    def onSell(self):
        self.sell_count += 1

    # separate interface from implementation details
    # onCandle should maintain logical states of all candle-related constraints
    @on('aggregator:new_candle')
    def onCandle(self, bar):
        self.num_bars += 1
        self.bars.append(bar)
        for rule in self.rules:
            self.refreshLogicStatus(rule, 'candle')
        if len(self.bars) > 1000:
            self.bars = self.bars[-1000:]

    # separate interface from implementation details
    # onPeriod should maintain logical states of all period-related constraints
    @on('aggregator:new_candle')
    def onPeriod(self, bar):
        timeToRefresh = False
        for rule in self.rules:
            logic_status = rule.logic_status.logic_status

            if 'period' not in logic_status.keys():
                continue
            else:
                period = logic_status['period'][1]
                activated_time = logic_status['period'][2]
                if self.num_bars - activated_time >= period:
                    timeToRefresh = True

            if timeToRefresh:
                self.refreshLogicStatus(rule, 'period')

    def refreshLogicStatus(self, rule, timeEvent):
        """
        refreshLogicStatus handles all changes in logic status of a rule
        due to the invocation of refresh functions.

        """

        logic_status = rule.logic_status.logic_status

        if timeEvent == 'candle':
            for cat, val in logic_status.items():
                if cat == 'bar':
                    rule.refresh(cat, self.num_bars)
        elif timeEvent == 'period':
            for cat, val in logic_status.items():
                if cat == 'period':
                    rule.refresh(cat, self.num_bars)

    def handleCheck(self, tick):
        """Wrapper function for calling check for each rule"""
        for code in self.rules:
            self.check(code)

    def check(self, rule):
        """Actual checking to deliver the required control flow"""
        logic_status = rule.logic_status.logic_status
        whenexec = rule.logic_status.whenexec
        dictionary = [constraint[1] for constraint in rule.logic_status.constraints]

        Flags = list(
            filter(
                lambda x: x['type'] == 'once per flag' or x['type'] == 'n per flag',
                dictionary,
            )
        )
        # pters is returning the list of self.func for all ocdblocks for checking
        pters = [item.func for item in self.rules]

        # Todo fix erratic behaviour
        # Currently, all lookup_check is void. No matter 'open'/'close, we only check when new
        # Candle is pushed (i.e. at open). However we guarantee that the
        # scheduler.last_open/scheduler.last_close is correct
        if self.lookup_check[whenexec] and all(
            lst[0] > 0 for key, lst in logic_status.items()
        ):
            # list comprehension to remove duplicates
            duplicate = [self.rules[pters.index(flag['funcpt'])] for flag in Flags]
            # augment duplicate with rules to pass into inidividual Rule
            augmented = [
                dict(t)
                for t in {
                    tuple((k, (v, d)) for k, v in d.flags.items()) for d in duplicate
                }
            ]
            rule.check(self.num_bars, augmented)

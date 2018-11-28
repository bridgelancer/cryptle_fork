from cryptle.event import source, on, Bus
from cryptle.codeblock import CodeBlock
from collections import OrderedDict


class Registry:
    """
    Registry class keeps record of the Strategy class's state information.

    It is also responsible for controlling the execution of logical tests
    at desired time and frequency as time elapsed.

    """

    def __init__(self, setup):
        # setup in conventional form - see test_registry.py for reference
        if all(len(item)>2 for x, item in setup.items()):
            self.setup = OrderedDict(sorted(setup.items(), key=lambda x: x[1][2]))
            self.codeblocks = list(map(CodeBlock, self.setup.keys(), self.setup.values()))
        else:
            self.setup = setup
        # in plain dictionary form, holds all logical states for limiting further triggering of
        self.check_order = [x for x in self.setup.keys()]

        # bar-related states that should be sourced from aggregator
        self.bars = []
        self.open_price = None # if last bar open price is required, reference to this
        self.close_price = None # if last bar close price is required, reference to this
        self.num_bars = 0
        self.new_open = False
        self.new_close = False
        # tick-related states that should be sourced from feed
        self.current_price = None
        self.current_time = None
        # trade-related states that should be sourced from OrderBook (or equivalent)
        self.buy_count = 0
        self.sell_count = 0
        self.lookup_check   = {'open': self.new_open,
                               'close': self.new_close,
                               '': True}

        for code in self.codeblocks:
            code.initializing()


    # Refresh methods to maintain correct states
    @on('tick') # tick should be agnostic to source of origin, but should take predefined format
    def refreshTick(self, tick):
        self.new_open = False
        self.new_close = False
        self.current_price = tick[0]
        self.current_time  = tick[2]
        self.updateLookUp()

    @on('aggregator:new_open') # 'open', 'close' events should be emitted by aggregator
    def refreshOpen(self, price):
        self.new_open = True
        self.open_price = price
        self.updateLookUp()

    @on('aggregator:new_close') # 'open', 'close' events should be emitted by aggregator
    def refreshClose(self, price):
        self.close_price = price
        self.new_close = True
        self.updateLookUp()

    def updateLookUp(self):
        self.lookup_check   = {'open': self.new_open,
                               'close': self.new_close,
                               '': True}

    # these flags are still largely imaginary and are not tested
    @on('buy') # 'buy', 'sell' events are not integrated for the moment
    def refreshBuy(self):
        self.buy_count += 1

    # these flags are still largely imaginary and are not tested
    @on('sell') # 'buy', 'sell' events are not integrated for the moment
    def refreshSell(self):
        self.sell_count += 1

    # refreshCandle should maintain logical states of all candle-related constraints
    @on('aggregator:new_candle')
    def refreshCandle(self, bar):
        self.num_bars += 1
        self.bars.append(bar)
        # this calls handleLogicStatus, which would remove all the 'once per bar' and 'n per bar' constraint for every candle
        for codeblock in self.codeblocks:
            self.handleLogicStatus(codeblock, 'candle')
        if len(self.bars) > 1000:
            self.bars = self.bars[-1000:]

    # refreshPeriod should maintain logical states of all period-related constraints
    @on('aggregator:new_candle')
    def refreshPeriod(self, bar):
        timeToRefresh = False
        for codeblock in self.codeblocks:
            logic_status = codeblock.logic_status.logic_status

            if 'period' not in logic_status.keys():
                continue
            else:
                period         = logic_status['period'][1]
                activated_time = logic_status['period'][2]
                if self.num_bars - activated_time >= period:
                    timeToRefresh = True

            if timeToRefresh:
                self.handleLogicStatus(codeblock, 'period')

    def handleLogicStatus(self, codeblock, timeEvent):
        """
            handleLogicStatus handles all changes in logic status of a codeblock
            due to the triggering ofrefresh functions.

        """

        logic_status = codeblock.logic_status.logic_status

        if timeEvent == 'candle':
            for cat, val in logic_status.items():
                if cat == 'bar':
                    codeblock.refreshing(cat, self.num_bars)
        elif timeEvent == 'period':
            for cat, val in logic_status.items():
                if cat == 'period':
                    codeblock.refreshing(cat, self.num_bars)


    @on('tick')
    def handleCheck(self, tick):
        """Wrapper function for calling check for each codeblock"""
        for code in self.codeblocks:
            self.check(code)

    def check(self, codeblock):
        # need to work on this -> whenexec not working as intended
        logic_status = codeblock.logic_status.logic_status
        whenexec = codeblock.logic_status.setup[0]
        triggerSetup = codeblock.logic_status.setup[1][0]
        dictionary = codeblock.logic_status.setup[1][1]

        Flags = []
        if 'once per signal' in dictionary:
            Flags = dictionary['once per signal']
        if 'n per signal' in dictionary:
            Flags += dictionary['n per signal']
        pters = [item.func for item in self.codeblocks]

        # Currently, all lookup_check is void. No matter 'open'/'close, we only check when new
        # Candle is pushed (i.e. at open). However we guarantee that the
        # registry.last_open/registry.last_close is correct
        if (self.lookup_check[whenexec] and \
            all(lst[0] > 0 for key, lst in logic_status.items()) and \
            all(all(self.codeblocks[pters.index(item[0])].flags.values()) for item in Flags)):
            # (pseudo-checing) whenexec
            # the current logic status of CodeBlock permits
            # all following flags of the signals return True

            codeblock.checking(self.num_bars)

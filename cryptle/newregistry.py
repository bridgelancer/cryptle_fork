from cryptle.event import source, on, Bus
from cryptle.codeblock import CodeBlock
from collections import OrderedDict

# BIG FIX NEEDED - To fix the behaviour of refreshSignals or come up with another idea to replace it
class Registry:
    """Registry class keeps record of the Strategy class's state information.
    It is also responsible for dispatching Events that signifiy the execution of logical tests
    at desired time and frequency as time elapsed.

    Args:
        setup (Dictionary): A Dictionary taking { 'actionname':
             [ [timing], \
             {constraints}, \
             order of execution (optional) ] }
        bus: Event Bus object
    """
    # Terminology used in in-line comments:
    #   client codes/tests = the functions of client codes which their behaviour are regulated by Registry
    #   whenexec           = the [0][0] of the value of setup.items() (str)
    #   triggerConstraints = the [0][1] of the value of setup.items() (dict)
    #   logical states     = the key-value pairs of logic_status (dict)

    #   refresh method     = all methods started with "refresh" - updating relevant states
    #   constraint method  = all methods placed below the ###CONSTRAINT FUNCTIONS### - apply relevant constraints to client codes
    #   check   (verb)     = refers to checking whether to execute a block of client codes registered in Registry
    #   execute (verb)     = refers to emitting 'registry:execute' to execute the block of client codes
    #   trigger (verb)     = refers to a successful run of client codes that emits
    #                        'strategy:triggered' or any execution of signal

    def __init__(self, setup):
        # setup in conventional form - see test_registry.py for reference
        if all(len(item)>2 for x, item in setup.items()):
            self.setup = OrderedDict(sorted(setup.items(), key=lambda x: x[1][2]))
            self.codeblocks = list(map(CodeBlock, self.setup.keys(), self.setup.values()))
        else:
            self.setup = setup
        # in plain dictionary form, holds all logical states for limiting further triggering of
        self.logic_status = {key: {} for key in setup.keys()}
        self.check_order = [x for x in self.setup.keys()]

        # bar-related states that should be sourced from aggregator
        self.bars = []
        self.open_price = None
        self.close_price = None
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
                               'close': self.new_close,}

        for code in self.codeblocks:
            code.initialize()


    # Refresh methods to maintain correct states
    @on('tick') # tick should be agnostic to source of origin, but should take predefined format
    def refreshTick(self, tick):
        self.new_open = False
        self.new_close = False
        self.current_price = tick[0]
        self.current_time  = tick[2]
        print('refreshTick', self.new_open)

    @on('aggregator:new_open') # 'open', 'close' events should be emitted by aggregator
    def refreshOpen(self, price):
        self.new_open = True
        self.open_price = price
        print('refreshOpen', self.new_open, "\n")

    @on('aggregator:new_close') # 'open', 'close' events should be emitted by aggregator
    def refreshClose(self, price):
        self.close_price = price
        self.new_close = True

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
        for key in self.logic_status.keys():
            self.handleLogicStatus(key, 'candle')
        if len(self.bars) > 1000:
            self.bars = self.bars[-1000:]

    # refreshPeriod should maintain logical states of all period-related constraints
    @on('aggregator:new_candle')
    def refreshPeriod(self, bar):
        timeToRefresh = False
        for key in self.logic_status.keys():
            if 'period' not in self.logic_status[key]:
                continue
            elif 'period' in self.logic_status[key]:
                period         = self.logic_status[key]['period'][1]
                activated_time = self.logic_status[key]['period'][2]
                if self.num_bars - activated_time >= period:
                    timeToRefresh = True
            if timeToRefresh:
                self.handleLogicStatus(key, 'period')

    # refreshSignal should maintain logical states of all signal-related constraints
    @on('signal') # 'signal' event could be any arbirtary flags generated by the client code, name not standardized at the moment
    def refreshSignal(self, signal):
        signalToRefresh = False
        applyConstraint = False
        # the return value of the 'signal' event generated by client code should be a list with
        # first item be the name of signal regestered as the signalConstraint of some other client
        # and second item be the boolean status of the signal.
        signalname, boolean = signal

        # Iterating over all items in the setup using the key
        for key, item in sorted(self.logic_status.items(), key=lambda x: self.check_order.index(x[0])):
            #print(signalname, key, item)
            #print(key, item)
            #print(signalname)

            if signalname in item:
                #print(signalname, item, self.logic_status[key][signalname][0])
                # call refreshLogicStatus if signal returned false
                if not boolean and self.logic_status[key][signalname][0] != -1:
                    signalToRefresh = True
                # apply suitable constraint if signal returned true and the test is locked
                if boolean and self.logic_status[key][signalname][0] == -1 or self.logic_status[key][signalname] == {}:
                    applyConstraint = True
            # cleanup actions resulting from the actions of refreshing signal
            if signalToRefresh:
                self.handleLogicStatus(key, signalname)
            if applyConstraint:
                # dictionary here is the dictionary within the string
                dictionary = self.setup[key][2][1]
                # we get the key in the dictionary that depends on the
                # previous actions, i.e. once per signal which depends on doneInit
                keyss = [v[0] for v in dictionary.items() if signalname in [w[0] for w in v[1]]]
                valuess = [v[1] for v in dictionary.items() if signalname in [w[0] for w in v[1]]]
                if len(keyss) > 0:
                    # keyss[-1] is the signal that passed and we want to tell
                    # the actions that depend on it
                    # constraint is a function referring to the keyss[-1] function
                    # in the lookup_trigger
                    # we give it the keyss[-1] function the items of keyss[-1]
                    constraint = self.lookup_trigger[keyss[-1]]
                    if keyss[-1] == 'once per signal':
                        constraint(key, signalname)
                    elif keyss[-1] == 'n per signal':
                        #print('fuck it', [x for x in dictionary[keyss[-1]] if x[0] == signalname])
                        constraint(key, *[x for x in dictionary[keyss[-1]] if x[0] == signalname])

    # timeEvent and signalname inconsistent
    def handleLogicStatus(self, key, timeEvent):
        # Draft hierachy - bar < period < trade < someshit(s) or < someshit(s) < trade? (or customizable?)
        # In any way, when ambiguous -> always take the most lenient one as the one with lowest # hierachy, bar < period < anythng is not ambiguous

        # For any given trigger constraint, the format needs to follow the following
        # specification: a dictionary with a string as key to specify constraint category and a
        # list as value.

        # The current format is: {'cat_name': [permissible number + 1,
        # of bar/trade/signal, time of initiating constraint]
        # e.g. {'bar': [1, 1, 2], 'period': [2, 3, 2], 'trade': [4, 4, 2], 'signal1': [5, 1, 1], 'signal2':
        # [6, 2, 10]}

        # The permissible number of triggering would be updated after there is a successful trigger
        # of the test by calling the constraint function. Whether or not a subsequent trigger is blocked depends on the
        # status of the logic status.

        # These codes basically removes the timeEvent from self.logic_status of that key, thereby
        # removing any constraint relevant to that cat
        test = self.logic_status[key]
        if timeEvent == 'candle':
            test = {cat:val for cat, val in test.items() if cat != 'bar'}
            self.logic_status[key] = test
        elif timeEvent == 'period':
            test = {cat:val for cat, val in test.items() if cat != 'period'}
            self.logic_status[key] = test

        # This control flow is hardcoded - any signal or trade Event that blocks further triggering
        # of client codes would be the only relevant condition for this temporary implementation. Only
        # reversal of that signal/trade event could lead to another execution of client codes. In the future,
        # an explicit hierachy structure should be implemented to clearly state the behaviour
        # instead of relying on the constraint functions and refresh functions to achieve a
        # more fine-grained control of the execution of client codes.
        else:
            # the logic_status of the client test would be rewritten to 'signalName": [-1, args*],
            # any subsequent triggering requires a refresh of this signal (hardcoded in constraint
            # functions)

            # basically set the count to -1
            self.logic_status[key] = {cat:[-1] + [x for i, x in enumerate(val) if i != 0] for cat, val in test.items() if cat == timeEvent}

    @on('tick')
    def handleCheck(self, tick):
        for code in self.codeblocks:
            setup = code.logic_status.setup
            self.check(code, setup[0], setup[1][0], code.logic_status)

    def check(self, codeblock, whenexec, triggerSetup, LogicStatus):
        print(LogicStatus.logic_status)
        if (#self.lookup_check[whenexec] and \
            all(lst[0] > 0 for key, lst in LogicStatus.logic_status.items())):
            codeblock.checking()


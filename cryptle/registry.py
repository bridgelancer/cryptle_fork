from cryptle.event import source, on

class Registry:
    '''Registry class keeps record of the various important state information for the Strategy
    class. Registry is also responsible for dispatching Events that signifiy the execution of logical tests
    at desired time and frequency as time elapsed.

    Args:
        setup (Dictionary): {'actionname': [[when to execute], {constraints after triggered}, order
        of execution (optional)]}

    Registry would control the order and when these logical tests execute. The client codes of the Strategy class
    should only execute when they receive their corresponding "registry:execute" signals. Different
    "registry:execute" signals are discerned by the first item in the list returned. The Signals
    are "triggered" if their test return True. In this situation, triggered tests of the client should
    emit a "strategy:triggered" event with its name (in string) as the associated value.
    '''
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
        self.setup = setup
        # in plain dictionary form, holds all logical states for limiting further triggering of
        self.logic_status = {key: {} for key in setup.keys()}

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
        # key-value pair with class method as value to predefined name of contraints
        self.lookup_trigger = {'once per bar': self.once_per_bar,
                               'once per trade': self.once_per_trade,
                               'once per period': self.once_per_period,
                               'once per signal': self.once_per_signal,
                               'n per bar': self.n_per_bar,
                               'n per period': self.n_per_period,
                               'n per trade': self.n_per_trade,
                               'n per signal': self.n_per_signal}

    # Refresh methods to maintain correct states
    @on('tick') # tick should be agnostic to source of origin, but should take predefined format
    def refreshTick(self, tick):
        self.new_open = False
        self.new_close = False
        self.lookup_check   = {'open': self.new_open,
                               'close': self.new_close,}
        self.current_price = tick[0]
        self.current_time = tick[2]

    @on('aggregator:new_open') # 'open', 'close' events should be emitted by aggregator
    def refreshOpen(self, price):
        self.new_open = True
        self.lookup_check   = {'open': self.new_open,
                               'close': self.new_close,}
        self.open_price = price

    @on('aggregator:new_close') # 'open', 'close' events should be emitted by aggregator
    def refreshClose(self, price):
        self.close_price = price
        self.new_close = True
        self.lookup_check   = {'open': self.new_open,
                               'close': self.new_close,}

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
                activated_time = self.logic_status[key]['period'][2]
                period         = self.logic_status[key]['period'][1]
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
        # semi-hardcoded behaviour, hierachy structure to be implemented
        for key in self.logic_status.keys():
            if signalname in self.logic_status[key]:
                # call refreshLogicStatus if signal returned false
                if not boolean and self.logic_status[key][signalname][0] != -1:
                    signalToRefresh = True
                # apply suitable constraint if signal returned true and the test is locked
                if boolean and self.logic_status[key][signalname][0] == -1:
                    applyConstraint = True
            # cleanup actions resulting from the actions of refreshing signal
            if signalToRefresh:
                self.handleLogicStatus(key, signalname)
            if applyConstraint:
                dictionary = self.setup[key][1][1]
                item = [k for k,v in dictionary.items() if v[0] == signalname]
                constraint = self.lookup_trigger[item[-1]]
                constraint(key, *dictionary[item[-1]])

    def handleLogicStatus(self, key, timeEvent):
        # Draft hierachy - bar < period < trade < someshit(s) or < someshit(s) < trade? (or customizable?)
        # In any way, when ambiguous -> always take the most lenient one as the one with lowest # hierachy, bar < period < anythng is not ambiguous

        # For any given trigger constraint, the format needs to follow the following
        # specification: a dictionary with a string as key to specify constraint category and a
        # list as value.

        # The current format is: {'cat_name': [permissible number + 1, # of bar/trade/signal, time
        # of initiating constraint]
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
        # an explicit hierachy structure should be implemented to clearly state the behaviour instead of relying the
        # constraint functions and refresh functions to achieve a more fine-grained control of the execution of client codes.
        else:
            # the logic_status of the client test would be rewritten to 'signalName": [-1, args*],
            # any subsequent triggering requires a refresh of this signal (hardcoded in constraint
            # functions)
            self.logic_status[key] = {cat:[-1] + [x for i, x in enumerate(val) if i != 0] for cat, val in test.items() if cat == timeEvent}

    # emitExecute push execute Event to Bus of the client
    @source('registry:execute')
    def emitExecute(self, key):
        # temporary return format for backtesting purposes, may consider revamping
        return [str(key), self.current_time, self.current_price]

    # On arrival of tick, handleCheck calls check and carries out checking
    @on('tick')
    def handleCheck(self, tick):
        if any(len(k[1]) < 3 for k, item in self.setup.items()):
            # for unspecified/incomplete order, the test would be run according to alphabetical
            # order of test keys
            for k, test in sorted(self.setup.items()):
                self.check(k, test[0], self.logic_status[k])
        else:
            # execute the tests in setup in predefined order specified by the int of test[1][2]
            for k, test in sorted(self.setup.items(), key=lambda test: test[1][2]):
                self.check(k, test[0], self.logic_status[k])

    # check should be able to enforce all constraints of client codes/tests against setup and logic
    # status and emit 'registry:execute'
    def check(self, key, whenexec, triggerConstraints):
        if (all(self.lookup_check[constraint] for constraint in whenexec) and
           (all(triggerConstraints[constraint][0] > 1 for constraint in triggerConstraints) or
               (triggerConstraints == {}))):
                # emitExecuted would be called if
                # 1.  Fulfilled constraint in whenexec
                # 2.  Either all triggerConstraints allow execution or no triggerConstraint present
                self.emitExecute(key)

    # handleTrigger handles all the triggered client tests and apply suitable constraints via constraint functions
    @on('strategy:triggered')
    def handleTrigger(self, action):
        # for updating constraints in the list of setup[1]
        for item in self.setup[action][1][0]:
            # reference of the constraint function stored in self.lookup_trigger
            constraint = self.lookup_trigger[item]
            constraint(action)
        # for updating constraints in the dictionary of the setup[1]
        for item in self.setup[action][1][1].keys():
            # reference of the constraint function stored in self.lookup_trigger
            constraint = self.lookup_trigger[item]
            constraint(action, *self.setup[action][1][1][item])

    ##################################CONSTRAINT FUNCTIONS##################################
    # These are the functions that are called by handleTrigger by iterating through the items of the
    # list and keys of the dictionary of triggerConstraints
    def once_per_bar(self, action):
        if 'bar' not in self.logic_status[action].keys():
            self.logic_status[action]['bar'] = [1, 1, self.num_bars]
        else:
            self.logic_status[action]['bar'][0] -= 1

    def n_per_bar(self, action, *args):
        if 'bar' not in self.logic_status[action].keys():
            self.logic_status[action]['bar'] = [*args, 1, self.num_bars]
        else:
            self.logic_status[action]['bar'][0] -= 1

    def once_per_period(self, action, *args):
        if 'bar' not in self.logic_status[action].keys():
            self.logic_status[action]['period'] = [1, *args, self.num_bars]
        else:
            self.logic_status[action]['period'][0] -=1

    def n_per_period(self, action, *args):
        if 'period' not in self.logic_status[action].keys():
            self.logic_status[action]['period'] = [*args, self.num_bars]
        else:
            self.logic_status[action]['period'][0] -= 1

    def once_per_trade(self, action):
        if 'period' not in self.logic_status[action].keys():
            self.logic_status[action]['trade'] = [1, 1, self.num_bars]
        else:
            self.logic_status[action]['trade'][0] -= 1

    def n_per_trade(self, action, *args):
        if 'trade' not in self.logic_status[action].keys():
            self.logic_status[action]['trade'] = [*args, 1, self.num_bars]
        else:
            self.logic_status[action]['trade'][0] -= 1

    def once_per_signal(self, action, signal, *args):
        if signal in self.logic_status[action].keys():
            # enter via refreshSignal
            if self.logic_status[action][signal][0] == -1:
                del self.logic_status[action][signal]
            else:
                self.logic_status[action][signal][0] -= 1
        elif signal not in self.logic_status[action].keys():
            self.logic_status[action][signal] = [1, 1, self.num_bars]

    # not tested
    def n_per_signal(self, action, signal, *args):
        print("BEFORE", self.logic_status[action])
        if signal in self.logic_status[action].keys():
            # enter via refreshSignal
            if self.logic_status[action][signal][0] == -1:
                del self.logic_status[action][signal]
            else:
                self.logic_status[action][signal][0] -= 1
        elif signal not in self.logic_status[action].keys():
            self.logic_status[action][signal] = [*args, 1, self.num_bars]
        print("AFTER", self.logic_status[action])

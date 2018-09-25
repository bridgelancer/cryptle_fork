from cryptle.event import source, on

class Registry:
    '''Registry class that keeps record of the various important state information for the Strategy
    class.

    Registry is also responsible for dispatching Events that signifiy the execution of logical tests
    at desired time and frequency as time elapsed.

    These functionality are achieved by three distinct types of functions within the Registry. The
    first type of functions handles market events (e.g. new bar, new tick, new open, new close).
    These maintain a valid state for the strategy and form the basis of the Registry class.

    The registry also holds functions that keep track of the orders that were placed by Strategy (or
    in the future, any OrderBook or equivalent). This allows the strategy to know the state of
    orders that it has placed previously and react accordingly.

    In order to streamline the process of generating valid logical tests for determining appropriate
    entries and exits based on any metric, the Registry is also responsible for regulating the
    execution of these logic tests at appropriate time. This is achieved by utilizing the state
    storing capacity of the Registry and the interaction between the Strategy and Registry class via
    the new EventBus architecture.

    In most of the cases, the logical tests of a bar-based strategy should not be indefinitely
    executable within the same bar. In the old Strategy implementation, this behaviour is achieved
    by creating flags held by the strategy class itself. This paradigm has proven to be useful in
    the development of simple strategy. However, as Cryptle progresses, the excessive flags and
    logic within the Strategy makes development hard and the code base unmaintainable.

    In view of these challenges, Registry would dictate when these logical tests should execute. The logical
    tests of the Strategy class should only execute when they receive their corresponding "registry:test" signals.
    Signals are "triggered" if their test return True. In this situation, triggered tests should generate a
    "strategy:triggered" event with its name (in string) as the associated value.

    '''
    def __init__(self, setup):
        self.setup = setup # setup should have str(actioname) as keys and a list of two lists as
                           # values {'actioname': [[argv to indicate when to execute],[constraints
                           # after being triggered]]
        self.logic_status = {key: [] for key in setup.keys()}
        self.num_bars = 0
        self.new_open = None
        self.new_close = None
        self.buy_count = 0
        self.sell_count = 0
        self.lookup_check   = {'open': self.new_open,
                               'close': self.new_close,}
        self.lookup_trigger = {'once per bar': self.once_per_bar,
                               'once per trade': self.once_per_trade,}
        self.open_price = None
        self.close_price = None
        self.current_price = None


    @on('tick')
    def refreshTick(self, price):
        self.new_open = False
        self.new_close = False
        self.current_price = price

    @on('open')
    def refreshOpen(self, price):
        self.new_open = True
        self.num_bars += 1
        self.open_price = price

    @on('close')
    def refreshClose(self, price):
        self.close_price = price
        self.new_close = True

    @on('buy')
    def refreshBuy(self):
        self.buy_count += 1

    @on('sell')
    def refreshSell(self):
        self.sell_count += 1

    # This handles all the execution of tests at appropriate time
    @on('tick')
    def handleCheck(self, price):
        setup = self.setup
        for key in setup.keys():
            # all items in setup[key][0] should be parsed to corresponding handle nested function in
            # checkXXX function
            eventName = 'registry:'+ str(key)
            @source(eventName)
            def check(whenexec):
                if all(self.lookup_check[constraint] for constraint in whenexec) and \
                   self.logic_status[key] == []: # now only works if no constraint is placed
                    return 'execute'
            check(setup[key][0])

    # This handles all the triggered tests and apply suitable constraints via constraint functions
    @on('strategy:triggered')
    def handleTrigger(self, action):
        def onTrigger(prohibited):
            for item in prohibited:
                constraint = self.lookup_trigger[item]
                constraint(action)
        onTrigger(self.setup[action][1])

    # constraint function after triggering, consider revamping into handleTrigger altogether
    def once_per_bar(self, action):
        # This function should be invoked if any action-setup pair in self.setup has been
        # triggered. This should prohibit any furthered triggering of the same action within the same bar
        # unless an explicit reversal is conveyed to the Registry, or a new bar is due.

        self.logic_status[action].append('once per bar')


    def once_per_trade(self, action):
        # This funciton should be invoked if any aciton setup pair in self.setup has been
        # executed. This hould prohibit any further triggering of the same action within the same trade
        # unless an explicit reversal is conveyed to the Registry, or the current position is
        self.logic_status[action].append('once per trade')

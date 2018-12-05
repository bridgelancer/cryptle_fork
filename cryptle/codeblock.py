class LogicStatus:
    """
    A wrapper snippet of the logic_status dictionary to provide utility for maintaining and
    determining the executability of a CodeBlock

    Args
    ---
    setup        : list
        The list corresponds to the the CodeBlock currently holds
    logic_status :  dictionary
        Local logical status of the codeblock to determine excutability by Registry

    The inner workings are relevant to developer for new types of constraints. Specifically, the
    individual constraint functions are defined within the LogicStatus class. They provide interface
    for CodeBlocks/Registry to update the values of the local logic_status at appropriate time. The
    control flow of these behaviour.

    """

    def __init__(self, setup, logic_status):
        self.setup        = setup
        self.logic_status = logic_status
        self.lookup_trigger = {
                               'once per bar': self.once_per_bar,
                               'once per trade': self.once_per_trade,
                               'once per period': self.once_per_period,
                               'once per flag': self.once_per_flag,
                               'n per bar': self.n_per_bar,
                               'n per period': self.n_per_period,
                               'n per trade': self.n_per_trade,
                               'n per flag': self.n_per_flag
                               }
        self.lookup_logic = {
                             'bar': ['once per bar', 'n per bar'],
                             'period': ['once per period', 'n per period'],
                             'trade': ['once per trade', 'n per trade'],
                             'flag': ['once per flag', 'n per flag']
                             }

    def is_executable(self):
        assert all(len(item) == 3 for item in self.logic_status.values()) and \
            all(all(isinstance(val, int) for val in item) for k, item in self.logic_status.items())

        if all(item[0] > 0 for k, item in self.logic_status.items()):
            return True
        else:
            return False

    # provide interface for resetting the logic_status back to default setup status
    def reset(self, resetConstraint, num_bars):
        """Reset specific constriant at certain num_bars to setup status"""
        if resetConstraint in self.logic_status.keys():
            del self.logic_status[resetConstraint]

            key = set(self.lookup_logic[resetConstraint]).intersection(
                set(self.setup[1][0] + list(self.setup[1][1].keys())))

            key = key.pop()
            if key in self.setup[1][0]:
                constraint = self.lookup_trigger[key]
                constraint(num_bars)
            if key in self.setup[1][1].keys():
                constraint = self.lookup_trigger[key]
                constraint(*self.setup[1][1][key], num_bars=num_bars)

    def callAll(self, num_bars):
        """Call all constraint functions at the num_bars. Called during initialization and refreshing"""
        for item in self.setup[1][0]:
            constraint = self.lookup_trigger[item]
            constraint(num_bars)
        for key, flags in self.setup[1][1].items():
            constraint = self.lookup_trigger[key]
            constraint(*flags, num_bars=num_bars)

    ##################################CONSTRAINT FUNCTIONS##################################
    def once_per_bar(self, num_bars):
        if 'bar' not in self.logic_status.keys():
            self.logic_status['bar'] = [1, 1, num_bars]


    def n_per_bar(self, *args, num_bars):
        if 'bar' not in self.logic_status.keys():
            self.logic_status['bar'] = [*args, 1, num_bars]
        else:
            self.logic_status['bar'][0] -= 1


    def once_per_period(self, *args, num_bars):
        if 'bar' not in self.logic_status.keys():
            self.logic_status['period'] = [1, *args, num_bars]


    def n_per_period(self, *args, num_bars):
        if 'period' not in self.logic_status.keys():
            self.logic_status['period'] = [*args, num_bars]
        else:
            self.logic_status['period'][0] -= 1


    def once_per_trade(self, num_bars):
        if 'trade' not in self.logic_status.keys():
            self.logic_status['trade'] = [1, 1, num_bars]


    def n_per_trade(self, *args, num_bars):
        if 'trade' not in self.logic_status.keys():
            self.logic_status['trade'] = [*args, num_bars]
        else:
            self.logic_status['trade'][0] -= 1


    def once_per_flag(self, codeblock, flag, *args, num_bars):
        if flag not in self.logic_status.keys():
            self.logic_status[flag] = [1, 1, num_bars]


    def n_per_flag(self, lst, *args, num_bars):
        if lst[1] in self.logic_status:
            self.logic_status[lst[1]][0] -= 1
        else:
            self.logic_status[lst[1]] = [lst[2], 1, num_bars]


class CodeBlock:
    """
    CodeBlocks are objects to be maintained by a Registry. They are created from the combination of
    a function pointer of client Strategy method and additional setup metainfo as dictated by the
    client. The format of passing the setup metainfo to Registry is documented in PivotStrat.

    Augments the client functions to maintain its own logic status and maintian its state
    transitions. Currently this is achieved via transitions.Machine but this introduces significant
    overhead to the computational speed of the programme. Future revamp would be underatken to
    address this issue and major revision is expected.

    Args
    ---
    functpt: reference to strategy method.
        The key of the setup dictionary entry that maps to the setup info of this CodeBlock
    setup: list
        The value of the setup dictionary entry that corresponds to the funcpt key of this CodeBlock


    Also provides a public interface for setting the localdata of one CodeBlock via the setLocalData
    method.

    """

    def __init__(self, funcpt, setup):
        self.name = funcpt.__name__
        self.func = funcpt
        self.logic_status = LogicStatus(setup, {})
        self.triggered = False
        self.last_triggered = None
        self.flags = {}
        self.localdata = {}

    # run initialization for each item in Registry.codeblocks
    def initialize(self):
        # codes that are really used for initialize the logical status based on the setup info
        """Initialize the logic_status of the local CodeBlock at num_bars as 0."""
        self.logic_status.callAll(0)

    def check(self, num_bars, flagvalues):
        """Update CodeBlock metainfo after client method returns. Cascading state changes."""
        self.triggered, self.flags, self.localdata = self.func(*flagvalues, **self.localdata)

        if self.triggered:
            self.last_triggered = num_bars
            self.update(num_bars)

    def update(self, num_bars):
        """Maintain the local logic_status while it is triggered at current num_bars"""
        self.logic_status.callAll(num_bars)

    def refresh(self, resetConstraint, num_bars):
        """
        Maintain the local logic_status while it is refreshed, reset against the passed
        constraintconstraint
        """
        self.logic_status.reset(resetConstraint, num_bars)

    def setLocalData(self, dictionary):
        """Public interface for client function to access other CodeBlocks localdata"""
        for k, v in dictionary.items():
            if k in self.localdata.keys():
                self.localdata[k] = v
            else:
                raise ValueError('Only for resetting existing values of localdata of a CodeBlock.')

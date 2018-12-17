from collections import ChainMap

class LogicStatus:
    """
    A wrapper snippet of the logic_status dictionary to provide utility for maintaining and
    determining the executability of a CodeBlock

    Args
    ---
    whenexec     : tuple
        The intended time of execution
    constraints  : tuple
        The logical constraints imposed on and flags that the CodeBLock could access to

    The inner workings are relevant to developer for developing new types of constraints. Specifically, the
    individual constraint functions are defined within the LogicStatus class. They provide interface
    for CodeBlocks/Registry to update the values of the local logic_status at appropriate time.

    """

    def __init__(self, whenexec, constraints):
        self.whenexec           = whenexec
        self.constraints        = tuple(constraints)
        self.logic_status       = {}
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

    #def is_executable(self):
    #    """Basic checking for whether the logic_status is compatible with design and excutable"""
    #    assert all(len(item) == 3 for item in self.logic_status.values()) and \
    #        all(all(isinstance(val, int) for val in item) for k, item in self.logic_status.items())

    #    if all(item[0] > 0 for k, item in self.logic_status.items()):
    #        return True
    #    else:
    #        return False

    def reset(self, resetConstraint, num_bars):
        """Reset specific constriant at certain num_bars to initial status"""
        if resetConstraint in self.logic_status.keys():
            del self.logic_status[resetConstraint]

            cat = set(self.lookup_logic[resetConstraint]).intersection(
                set([constraint[1]['type'] for constraint in self.constraints]))

            assert len(cat) == 1
            cat = cat.pop() # only 1 key would present by default

            if cat in [constraint[1]['type'] for constraint in self.constraints]:
                constraint_ft = self.lookup_trigger[cat]
                constraint_ft(cat, num_bars)

    def callAll(self, num_bars):
        """Call all constraint functions and pass num_bars as arg.

        Called during initialization and refreshing of Registry

        """

        for constraint in self.constraints:
            const_name = constraint[0]
            kws        = constraint[1]
            constraint_ft = self.lookup_trigger[kws['type']]
            constraint_ft(const_name, num_bars=num_bars, **kws) # determine how to pass the arguments into the constraints


    ##################################CONSTRAINT FUNCTIONS##################################
    def once_per_bar(self, const_name, num_bars, **kws):
        if 'bar' not in self.logic_status.keys():
            self.logic_status['bar'] = [1, 1, num_bars]


    def n_per_bar(self, const_name, num_bars, **kws):
        max_trigger = kws['max_trigger']
        if 'bar' not in self.logic_status.keys():
            self.logic_status['bar'] = [max_trigger, 1, num_bars]
        else:
            self.logic_status['bar'][0] -= 1


    def once_per_period(self, const_name, num_bars, **kws):
        kws['refresh_period'] = refresh_period
        if 'bar' not in self.logic_status.keys():
            self.logic_status['period'] = [1, refresh_period, num_bars]


    def n_per_period(self, const_name, num_bars, **kws):
        max_trigger = kws['max_trigger']
        refresh_period = kws['refresh_period']
        if 'period' not in self.logic_status.keys():
            self.logic_status['period'] = [max_trigger, refresh_period, num_bars]
        else:
            self.logic_status['period'][0] -= 1


    def once_per_trade(self, const_name, num_bars, **kws):
        if 'trade' not in self.logic_status.keys():
            self.logic_status['trade'] = [1, 1, num_bars]


    def n_per_trade(self, const_name, num_bars, **kws):
        max_trigger = kws['max_trigger']
        if 'trade' not in self.logic_status.keys():
            self.logic_status['trade'] = [max_trigger, 1, num_bars]
        else:
            self.logic_status['trade'][0] -= 1


    def once_per_flag(self, const_name, num_bars, **kws):
        if const_name not in self.logic_status.keys():
            self.logic_status[const_name] = [1, 1, num_bars]


    def n_per_flag(self, const_name, num_bars, **kws):
        max_trigger = kws['max_trigger']
        if const_name in self.logic_status:
            self.logic_status[const_name][0] -= 1
        else:
            self.logic_status[const_name] = [max_trigger, 1, num_bars]


class CodeBlock:
    """
    CodeBlocks are objects to be maintained by a Registry. They are created from a tuple
    corresponds to the the entry of the setup for that particular Stratey method.
    The format of passing the setup metainfo to Registry is documented in PivotStrat and guides.

    Augments the client functions to maintain its own logic status and maintian its state
    transitions. Also provides a public interface for setting the localdata of another CodeBlock
    via the :meth:`setLocalData` method by a Strategy method.

    Args
    ---
    functpt: reference to strategy method.
        The key of the setup dictionary entry that maps to the setup info of this CodeBlock
    setup: list
        The value of the setup dictionary entry that corresponds to the funcpt key of this CodeBlock

    """

    def __init__(self, *entry):
        func, *constraints = entry[0]

        self.name = func[1].__name__
        self.func = func[1]

        self.logic_status = LogicStatus(constraints[0][1], constraints[1:])
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
        """Update CodeBlock metainfo after client method returns"""
        flagValues, flagCB = unpackDict(*flagvalues)
        self.triggered, self.flags, self.localdata = self.func(flagValues, flagCB, **self.localdata)

        if self.triggered:
            self.last_triggered = num_bars
            self.update(num_bars)

    def update(self, num_bars):
        """Maintain the local logic_status while it is triggered at current num_bars"""
        self.logic_status.callAll(num_bars)

    def refresh(self, resetConstraint, num_bars):
        """
        Maintain the local logic_status while it is refreshed by Registry, reset against
        the passed constraint.
        """
        self.logic_status.reset(resetConstraint, num_bars)

    def setLocalData(self, dictionary):
        """Public interface for client function to access other CodeBlocks localdata"""
        for k, v in dictionary.items():
            if k in self.localdata.keys():
                self.localdata[k] = v
            else:
                raise ValueError('Only for resetting existing values of localdata of a CodeBlock.')

def unpackDict(*flagvalues):
    """Module function that handles the unpacking of flagvalues that Registry passed into CodeBlock"""
    flagTuple = dict(ChainMap(*flagvalues))
    flagValues = dict([(k, v[0]) for k, v in flagTuple.items()])
    flagCB = dict([(k, v[1]) for k, v in flagTuple.items()])
    return flagValues, flagCB

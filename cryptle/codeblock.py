from transitions import Machine

# Now each CodeBlock maintains its own logic status. Registry would directly maintain
# the LogicStatus of a CodeBlock as the states of the CodeBlock transition to one another.

class LogicStatus:
    """ A wrapper snippet of the logic_status dictionary to provide utility for determining
    the executability of a CodeBlock"""

    def __init__(self, setup, logic_status):
        self.setup        = setup
        self.logic_status = logic_status
        self.lookup_trigger = {#'once': self.once,
                               'once per bar': self.once_per_bar,
                               'once per trade': self.once_per_trade,
                               'once per period': self.once_per_period,
                               'once per signal': self.once_per_signal,
                               'n per bar': self.n_per_bar,
                               'n per period': self.n_per_period,
                               'n per trade': self.n_per_trade,
                               'n per signal': self.n_per_signal}

    def is_executable(self):
        assert self.logic_status == {} or len(self.logic_status) == 2 and \
            all(all(isinstance(value, int) for val in item) for k, item in self.logic_status.items())

        if all(item[0] > 0 for k, item in self.logic_status.items()):
            return True
        else:
            return False

    # provide interface for updating the logic_status
    def trigger(self, triggeredConstraint):
        constraint = self.lookup_trigger[resetConstraint]
        constraint()

    # provide interface for resetting the logic_status back to default setup status
    def reset(self, resetConstraint):
        if resetConstraint in self.logic_status.keys():
            del self.logic_status[resetConstraint]
            constraint = self.lookup_trigger[resetConstraint]
            constraint()

    # provide interface for flashing the whole logic_status to empty and reassigning
    def resetAll(self):
        self.logic_status = {}
        for item in self.setup[1][0]:
            constraint = self.lookup_trigger[item]
            constraint()
        for key, item in self.setup[1][1].items():
            constraint = self.lookup_trigger[key]
            constraint(*item)

    ##################################CONSTRAINT FUNCTIONS##################################
    def once_per_bar(self):
        if 'bar' not in self.logic_status.keys():
            self.logic_status['bar'] = [1, 1]

    def n_per_bar(self, *args):
        if 'bar' not in self.logic_status.keys():
            self.logic_status['bar'] = [*args, 1]
        else:
            self.logic_status['bar'][0] -= 1

    def once_per_period(self, *args):
        if 'bar' not in self.logic_status.keys():
            self.logic_status['period'] = [1, *args]

    def n_per_period(self, *args):
        if 'period' not in self.logic_status.keys():
            self.logic_status['period'] = [*args]
        else:
            self.logic_status['period'][0] -= 1

    def once_per_trade(self):
        if 'trade' not in self.logic_status.keys():
            self.logic_status['trade'] = [1, 1]

    def n_per_trade(self, *args):
        if 'trade' not in self.logic_status.keys():
            self.logic_status['trade'] = [*args]
        else:
            self.logic_status['trade'][0] -= 1

    def once_per_signal(self, signal, *args):
        if signal in self.logic_status.keys():
            if self.logic_status[signal][0] == -1:
                del self.logic_status[signal]
        elif signal not in self.logic_status.keys():
            self.logic_status[signal] = [1, 1]

    def n_per_signal(self, signal, *args):
        if signal[0] in self.logic_status:
            if self.logic_status[signal[0]][0] == -1:
                del self.logic_status[signal[0]]
            else:
                self.logic_status[signal[0]][0] -= 1
        elif signal[0] not in self.logic_status:
            self.logic_status[signal[0]] = [signal[1], 1]



class CodeBlock:
    """ CodeBlocks are classes to be maintained by a Registry when the function pointers of a
    Strategy are passed into Registry.

    Augments the client functions to maintain its own logic status and maintian its state transitions via
    transitions.Machine.

    """

    states =  ['initialized', 'rest', 'checked', 'executed', 'triggered']
    def __init__(self, funcpt, setup):
        self.name = funcpt.__name__
        self.func = funcpt
        self.logic_status = LogicStatus(setup, {})

        self.machine = Machine(model=self, states=CodeBlock.states, initial='initialized')

        # transition that a CodeBlock possesses; add suitable callbacks and
        # before/after/conditions/unless to transitions for controlling behaviour of codeblocks
        self.machine.add_transition(trigger='initialize', source='initialized', dest='rest',
                before='initialization')
        self.machine.add_transition(trigger='checking', source='rest', dest='executed',
                before=self.func)

        self.machine.add_transition(trigger='passTrigger', source='executed', dest='triggered')
        self.machine.add_transition(trigger='failTrigger', source='executed', dest='rest')

        self.machine.add_transition(trigger='cleanup', source='triggered', dest='rest',
                after='update')

    # run initialization for each item in Registry.codeblocks
    def initialization(self):
        # codes that are really used for initialize the logical status based on the setup info
        self.logic_status.resetAll()

    def update(self):
        pass



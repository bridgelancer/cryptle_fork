from transitions import Machine

# Now each CodeBlock maintains its own logic status. Registry would directly maintain
# the logic_status of the CodeBlock as the states of the CodeBlock transition to one another.


class CodeBlock:
    """ CodeBlocks are classes to be maintained by a Registry when the function pointers of a
    Strategy are passed into Registry.

    Augments the functions to maintain its own logic status and maintian its state transitions via
    transitions.Machine.

    """

    states =  ['initialized', 'rest', 'checked', 'executed', 'triggered']
    def __init__(self, funcpt, setup):
        self.name = funcpt.__name__
        self.logic_status = {}

        self.machine = Machine(model=self, states=CodeBlock.states, initial='initialized')

        # transition that a CodeBlock possesses; add suitable callbacks and
        # before/after/conditions/unless to transitions for controlling behaviour of codeblocks
        self.machine.add_transition(trigger='', source='initialized', dest='rest')
        self.machine.add_transition(trigger='', source='rest', dest='checked')

        self.machine.add_transition(trigger='', source='checked', dest='executed')
        self.machine.add_transition(trigger='', source='checked', dest='rest')

        self.machine.add_transition(trigger='', source='executed', dest='triggered')
        self.machine.add_transition(trigger='', source='executed', dest='rest')

        self.machine.add_transition(trigger='', source='triggered', dest='rest')


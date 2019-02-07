from inspect import getmembers, isclass, signature
from importlib import import_module
import sys

import click

from cryptle.strategy import TradingStrategy, SingleAssetStrategy

# Warning: These tests are largely provisionary and might vary in the future. They are also not yet
# implemeted for the moment.


def _pass() -> None:
    click.secho('Check passed. \n', fg='bright_green')


def _check(message: str) -> None:
    click.secho(message, fg='bright_green')


def _warn(message: str) -> None:
    click.secho(message, fg='yellow')


def _fail(message: str) -> None:
    click.secho(message, fg='bright_red')


def _parse_dir(string):
    """Remove the .py end and replace all / to ."""
    m = '.'.join(string.split('/'))
    return m[:-3]


class StratHolder:
    def __init__(self):
        from cryptle.exchange.paper import Paper
        from cryptle.strategy import Portfolio

        self.strat = None
        self.pair = 'btcusd'
        self.asset = 'btc'
        self.base_currency = 'usd'
        self.exchange = Paper(0, commission=0.0013, slippage=0)
        self.port = Portfolio(cash=10000, base_currency=self.base_currency)

    def defaultSetup(self):
        assert type(self.strat) is not None

        self.strat = self.strat(self.exchange, self.asset, pair=self.pair)
        self.strat.portfolio = self.port

        assert isinstance(self.strat, TradingStrategy)


pass_strat = click.make_pass_decorator(StratHolder, ensure=True)


@click.group(invoke_without_command=True)
@click.argument('filedir')
@pass_strat
@click.pass_context
def parse(ctx, holder, filedir):
    click.secho(
        '\nParsing path and importing file {}.'.format(filedir), fg='bright_cyan'
    )

    if '/' in filedir:
        filedir = _parse_dir(filedir)

    module = import_module(filedir)
    click.secho('Finished importing {}. \n'.format(filedir), fg='bright_cyan')

    strat_name, strat = None, None

    for name, obj in {
        name: obj for name, obj in module.__dict__.items() if isclass(obj)
    }.items():
        # currently hardcoded for existing base classes
        if (
            issubclass(obj, TradingStrategy) or issubclass(obj, SingleAssetStrategy)
        ) and obj.__module__ != 'cryptle.strategy':
            strat_name, strat = name, obj

    assert type(strat_name) == str
    assert type(strat) != None

    click.secho(
        'Found the Strategy class to be parsed: {} {}.'.format(strat_name, strat),
        fg='bright_yellow',
    )
    holder.strat = strat
    holder.defaultSetup()


@parse.command()
@pass_strat
@click.pass_context
def callTests(ctx, holder):
    """Calls all the Commands of parse group, except itself and the root"""
    commands = [
        i for i in getmembers(sys.modules[__name__]) if isinstance(i[1], click.Command)
    ]
    commands = filter(lambda x: (x[0] not in ['parse', 'callTests']), commands)

    click.secho('Checking starts...\n', fg='bright_yellow')
    for t in commands:
        ctx.invoke(t[1])


@parse.command()
@pass_strat
def superInit(holder):
    from cryptle.exchange.paper import Paper

    """Check whether the Strategy parent class initiator was called"""
    _check('Checking whether parent class __init__ was called.')
    strat = holder.strat

    for tup in getmembers(strat):
        name, obj = tup
        if isinstance(obj, Paper):
            _pass()
            return

    _fail('Please invoke the parent Strategy-derived base class constructor.')


@parse.command()
@pass_strat
def onEvent(holder):
    """Check whether the onEvent interface was implemented in Strategy for data
    handling"""
    _check('Checking whether onCandle or onTick is implemented.')
    strat = holder.strat

    for tup in getmembers(strat):
        name, obj = tup
        if name == 'onTrade' and callable(obj):
            _pass()
            return

        if name == 'onCandle' and callable(obj):
            _pass()
            return

    _fail(
        'onEvent method missing: please implement onEvent interface for data handling. \n'
    )


@parse.command()
@pass_strat
def aggregatorAndCandle(holder):
    """Check whether the scheduler and setup, if used, are both present in equal number"""
    from cryptle.aggregator import Aggregator
    from cryptle.metric.timeseries.candle import CandleStick

    _check('Checking number of Aggregator and CandleStick.')
    strat = holder.strat

    lst = []

    # Could also consider checking whether these aggregator/candle are of equal
    # period/lookback
    for tup in getmembers(strat):
        name, obj = tup
        if isinstance(obj, Aggregator) or isinstance(obj, CandleStick):
            lst.append(type(obj))

    d = {}
    for otype in lst:
        d[otype] = d.get(otype, 0) + 1

    if len(set(d.values())) <= 1:
        _pass()
    else:
        _fail('Please declare equal number of Aggregator and CandleStick')


@parse.command()
@pass_strat
def rule(holder):

    _check('Checking signature of rules.')
    strat = holder.strat

    function_lst = []
    for tup in getmembers(strat):
        name, obj = tup
        if name == 'scheduler':
            scheduler = obj
        if callable(obj):
            function_lst.append(obj)

    if scheduler is None:
        return

    # modify this func_lst to a list that contains the desired function signature

    param_lst = []
    correct_name_func_lst = []
    annotated_func_lst = []

    for func in function_lst:
        try:
            sig = signature(func)
            param_lst = [
                p
                for p in sig.parameters.values()
                if p.kind == p.POSITIONAL_OR_KEYWORD or p.POSITIONAL_ONLY
            ]

            names = [p.name for p in param_lst]
            annotations = [p.annotation for p in param_lst]

            if names == ['flagValues', 'flagCB']:
                correct_name_func_lst.append(func)
            if annotations == [type({}), type({})]:
                annotated_func_lst.append(func)
        except:
            pass

    correct_name_func_set = set(correct_name_func_lst)
    annotated_func_set = set(annotated_func_lst)
    cb_set = set([rule.func for rule in scheduler.rules])

    correct_name = correct_name_func_set.intersection(cb_set) == cb_set
    annotated = annotated_func_set.intersection(cb_set) == cb_set

    if correct_name and annotated:
        _pass()
    if not annotated:
        _warn('Please consider annoate the function appropriately \n')
    if not correct_name:
        _warn('Please consider follow the naming convention of rules \n')
    if not annotated and not correct_name:
        _fail('Please review the function signature and setup passed to scheduler\n')

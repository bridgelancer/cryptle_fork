import inspect
import json

def checkType(param, *types):
    valid_type = False

    for t in types:
        valid_type |= isinstance(param, t)

    if not valid_type:
        caller = inspect.stack()[1][3]
        passed = type(param).__name__

        fmt = "{} was passed to {}() where {} is expected"
        msg = fmt.format(passed, caller, types)

        raise TypeError(msg)


def unpackTick(tick):
    checkType(tick, dict)

    price = tick['price']
    volume = tick['amount']
    timestamp = float(tick['timestamp'])

    return price, volume, timestamp


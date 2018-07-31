# ===[ cryptle.py ]===
from functools import wraps

class Engine:
    # @Todo: strict_install
    # @Todo: strict_begin
    def _publish():

    def _subscribe():

    # @Rename
    def add():


def subscribe(*events):
    @wraps
    def decorator(func):
        func._hook = events
        return func
    return decorator


def publish(*events):
    @wraps
    def decorator(func):
        func._hook = events
        return func
    return decorator


class PluginMeta(type):
    def __new__(cls, name, bases, attrs):
        # Setup subscribe/publish hooks
        ...

    def __init__(cls, name, bases, attrs):
        # Handle class
        ...

class Plugin(metaclass=PluginMeta):
    # Handle
    def  __new__(self):
        # Handle
        ...


    def  __init__(self):
        # Handle
        ...


# ===[ foostrat.py ]===
from cryptle import Plugin, subscribe, publish

class FooStrat(Plugin):
  requires = []

  def __init__(self):

  @subscribe('<pair>:tick')
  def onTick(self, event):

  @publish('<pair>:buy')
  def buy(self, ):
     return

from cryptle.engine import on

class FooStrat(Plugin):
    require = ['time', '{pair}:candle']

    def __init__(self, pair):
        self.pair = pair

    @subscribe('event')
    def onEvent(self):
        pass

    @subscribe('time')
    def on15minutes(self):
        pass

    @publish(...)
    def hi():
        ...


# ===[ main.py ]===
if __name__ == '__main__':
    import cryptle.engine as engine
    config = {...}
    engine.install(FooStrat(config))
    engine.install()

# Raises dependency exception
    engine.start()

# Succeed
    engine.start()


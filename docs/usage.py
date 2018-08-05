# ===[ DI framework ]===
from cryptle.di import Component, require

class Car(Component):
    engine = require(Engine)
    frame = require(Frame)

    def start(self):
        self.frame.safetycheck()
        self.engine.fire()


# ===[ foostrat.py ]===
from cryptle.di import Component
from cryptle.ta import MA, RSI
from cryptle.mq import publish, subscribe

class FooStrat(Component):
    ma  = require(MA)
    rsi = require(RSI)

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

    # Raises dependency exception
    engine.start()

    from cryptle.ta import MA, RSI
    engine.install(MA(pair))
    engine.install(RSI(pair))

    # Succeed
    engine.start()


import time
from threading import Thread

from .event import source


SECOND = 1
MINUTE = 60
HOUR = 3600
DAY = 86400

RESOLUTION = 0.1


class Clock(Thread):
    """Emitter for events on passage of time. Inherits from standard library Thread.

    The following are events that will be emitted by a clock:
    - ``second(now)``
    - ``minute(now)``
    - ``hour(now)``
    - ``day(now)``

    """

    def __init__(self):
        super().__init__()
        self.keep_running = True

    def run(self):
        self.keep_running = True

        while self.keep_running:
            time.sleep(RESOLUTION)
            now = time.time()

            if now % SECOND < RESOLUTION:
                self.tic_second(now)

            if now % MINUTE < RESOLUTION:
                self.tic_min(now)

            if now % HOUR < RESOLUTION:
                self.tic_hour(now)

            if now % DAY < RESOLUTION:
                self.tic_day(now)

    def stop(self):
        self.keep_running = False

    @staticmethod
    @source('second')
    def tic_second(now):
        return now

    @staticmethod
    @source('minute')
    def tic_min(now):
        return now

    @staticmethod
    @source('hour')
    def tic_hour(now):
        return now

    @staticmethod
    @source('day')
    def tic_day(now):
        return now

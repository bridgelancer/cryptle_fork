class DatafeedException(Exception):
    pass

class ConnectionClosed(DatafeedException):
    pass

class BadMessage(DatafeedException):
    pass

class BadEvent(DatafeedException):
    pass

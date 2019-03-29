class ExchangeError(RuntimeError):
    pass


class OrderError(ExchangeError):
    pass


# Todo(alan): Semantically these order errors can be raised before an order ID is
# assigned. Refactor to better names.
class MarketOrderFailed(OrderError):
    """
    Args:
        oid: int - Order ID
    """

    def __init__(self, oid, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.id = oid


class LimitOrderFailed(OrderError):
    """
    Args:
        oid: int - Order ID
    """

    def __init__(self, oid, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.id = oid

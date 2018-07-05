import bisect


class Orderbook:
    """In memory orderbook.

    Args:
        bids: An array of tuples as [(price, volume), ...]
        asks: Same as bids
    """
    def __init__(self, bids=None, asks=None):
        self._bids = {}
        self._asks = {}
        self._time = -1

        # Duplicate data of order prices as list for sorted lookup performance
        self._bid_prices = []
        self._ask_prices = []

        if bids:
            for price, volume in bids:
                self._bid_prices.append(price)
                self._bids[price] = volume
            self._bid_prices.sort()

        if asks:
            for price, volume, in asks:
                self._ask_prices.append(price)
                self._asks[price] = volume
            self._ask_prices.sort()

    def create_bid(self, price, amount):
        """Place new bid order."""
        self.create(price, amount, 'bid')

    def create_ask(self, price, amount):
        """Place new ask order."""
        self.create(price, amount, 'ask')
    
    def take_bid(self, price, amount):
        """Remove a bid order as taken by a market order."""
        self.take(price, amount, 'bid')

    def take_ask(self, price, amount):
        """Remove an ask order as taken by a market order."""
        self.take(price, amount, 'ask')

    def delete_bid(self, price, amount):
        """Remove a bid order as deleted."""
        self.delete(price, amount, 'bid')

    def delete_ask(self, price, amount):
        """Remove an ask order as deleted."""
        self.delete(price, amount, 'ask')

    def create(self, price, amount, otype):
        if otype == 'bid':
            if price not in self._bid_price:
                bisect.insort(self._bid_prices, price)
                self._bids[price] = amount
            else:
                self._bids[price] += amount
        elif otype == 'ask':
            if price not in self._asks:
                bisect.insort(self._ask_prices, price)
                self._asks[price] = amount
            else:
                self._asks[price] += amount

    def take(self, price, amount, otype):
        if otype == 'bid':
            if price not in self._bids:
                raise ValueError('')
        elif otype == 'ask':
            if price not in self._asks:
                raise ValueError('')

    def delete(self, price, amount, otype):
        pass

    def apply_diff(self, price, amount, timestamp, diff_type, order_type):
        """Apply an orderdiff to the orderbook.
        
        Args:
            diff_type: Type of diff. Accepted values are 'create', 'take', 'delete'.
            order_type: Type of diffed order. Accepted values are 'bid', 'ask.
            
        Todo:
            - Consider using keyword args instead of dict arg
        """
        if order_type == 'bid':
            if diff_type == 'create':
                self.create_bid(price, amount)
            elif diff_type == 'take':
                self.take_bid(price, amount)
            elif diff_type == 'delete':
                self.delete_bid(price, amount)

        elif order_type == 'ask':
            if diff_type == 'create':
                self.create_ask(price, amount)
            elif diff_type == 'take':
                self.take_ask(price, amount)
            elif diff_type == 'delete':
                self.delete_ask(price, amount)
            
        self._time = timestamp

    def _order_exist(self, price):
        return price in self._bids or price in self._asks


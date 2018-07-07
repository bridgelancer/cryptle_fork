import bisect


class OrderRecord:
    """An entry in the orderbook. Not to be confused with an order.
    
    OrderRecord is an immutable dataclass for representing a row in the orderbook.

    Args:
        price: Unit price.
        volume: Volume.
    """
    def __init__(self, price, volume):
        self._price  = price
        self._volume = volume

    @property
    def price(self):
        return self._price

    @property
    def volume(self):
        return self._volume


class Orderbook:
    """In memory orderbook.

    Args:
        bids: An array of tuples as [(price, volume), ...]
        asks: Same as bids
    """
    def __init__(self, bids=None, asks=None, time=-1):
        self._bids = {}
        self._asks = {}
        self._time = time

        # Duplicate data of order prices as list for sorted lookup performance
        # These lists are to be mainted sorted after modifications
        self._bid_prices = []
        self._ask_prices = []

        if bids:
            for price, volume in bids:
                self._bid_prices.append(price)
                self._bids[price] = volume
            self._bid_prices.sort(reverse=True)

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

    def top_bid(self, n=1):
        """Returns top n number of bid prices."""
        return self._bid_prices[:n]

    def top_bid_volume(self, n=1):
        """Returns top n number of bid prices."""
        return [self._bids[price] for price in self._bid_prices[:n]]

    def top_bid_order(self, n=1):
        """Returns top n number of bid prices."""
        return [OrderRecord(price, self._bids[price]) for price in self._bid_prices[:n]]

    def top_ask(self, n=1):
        """Returns top n number of ask prices."""
        return self._ask_prices[:n]

    def top_ask_volume(self, n=1):
        """Returns top n number of ask prices."""
        return [self._asks[price] for price in self._ask_prices[:n]]

    def top_ask_order(self, n=1):
        """Returns top n number of ask prices."""
        return [OrderRecord(price, self._asks[price]) for price in self._ask_prices[:n]]

    @classmethod
    def fromstring(cls, bids, asks, time=-1):
        """Type flexible version of __init__. 
        
        Convert all values to float before putting them into internal storage.
        """
        self = cls()
        self._time = time

        for price, volume in bids:
            self._bid_prices.append(float(price))
            self._bids[float(price)] = float(volume)
        self._bid_prices.sort(reverse=True)

        for price, volume, in asks:
            self._ask_prices.append(float(price))
            self._asks[float(price)] = float(volume)
        self._ask_prices.sort()

        return self

    def _order_exist(self, price):
        return price in self._bids or price in self._asks

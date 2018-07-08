import bisect
from datetime import datetime


class OrderEntry:
    """An entry in the orderbook. Not to be confused with an order.
    
    OrderEntry is an immutable dataclass for representing a row in the orderbook.

    Args:
        price: Unit price.
        volume: Volume.
    """
    def __init__(self, price, volume):
        self._price  = price
        self._volume = volume

    def __repr__(self):
        return '<OrderEntry: ({}, {})>'.format(self._price, self._volume)

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
        time: Time of snapshot
    """
    def __init__(self, bids=None, asks=None, time=-1):
        self._bids = {}
        self._asks = {}
        self._time = time
        self._diff = 0

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

    def __repr__(self):
        return '<Orderbook (bid: {}, ask: {})>'.format(self.top_bid(), self.top_ask())

    @property
    def time(self):
        """Datetime of snapshot."""
        return datetime.fromtimestamp(self._time)

    @time.setter
    def time(self, time):
        if isinstance(time, (int, float)):
            self._time = time
        elif isinstance(time, datetime):
            self._time = datetime.timestamp()
        else:
            raise TypeError('Integer or datetime expected')

    def mid_price(self):
        """Mid price"""
        return (self.top_bid() + self.top_ask()) / 2

    def spread(self):
        """Bid-ask spread"""
        return self.top_ask() - self.top_bid()

    def create_bid(self, price, amount):
        """Place new bid order."""
        if price not in self._bids:
            bisect.insort(self._bid_prices, price)
            self._bids[price] = amount
        else:
            self._bids[price] += amount

    def create_ask(self, price, amount):
        """Place new ask order."""
        if price not in self._asks:
            bisect.insort(self._ask_prices, price)
            self._asks[price] = amount
        else:
            self._asks[price] += amount

    def take_bid(self, price, amount):
        """Remove a bid order as taken by a market order."""
        if price not in self._bids:
            raise ValueError('No existing bid order at ${}'.format(price))
        else:
            self._bids[price] -= amount
            if self._bid[price] < 0.0001:
                self._bids.pop(price)
                self._bid_prices.remove(price)

    def take_ask(self, price, amount):
        """Remove an ask order as taken by a market order."""
        if price not in self._asks:
            raise ValueError('No existing ask order at ${}'.format(price))
        else:
            self._asks[price] -= amount
            if self._asks[price] < 0.0001:
                self._asks.pop(price)
                self._ask_prices.remove(price)

    def delete_bid(self, price, amount):
        """Remove a bid order as deleted."""
        if price not in self._bids:
            raise ValueError('No existing bid order at ${}'.format(price))
        else:
            self._bids[price] -= amount
            if self._bids[price] < 0.001:
                self._bids.pop(price)
                self._bid_prices.remove(price)

    def delete_ask(self, price, amount):
        """Remove an ask order as deleted."""
        if price not in self._asks:
            raise ValueError('No existing ask order at ${}'.format(price))
        else:
            self._asks[price] -= amount
            if self._asks[price] < 0.0001:
                self._asks.pop(price)
                self._ask_prices.remove(price)

    def create(self, price, amount, otype):
        if otype == 'bid':
            self.create_bid(price, amount)
        elif otype == 'ask':
            self.create_ask(price, amount)

    def take(self, price, amount, otype):
        if otype == 'bid':
            self.take_bid(price, amount)
        elif otype == 'ask':
            self.take_ask(price, amount)

    def delete(self, price, amount, otype):
        if otype == 'bid':
            self.delete_bid(price, amount)
        elif otype == 'ask':
            self.delete_ask(price, amount)

    def apply_diff(self, price, amount, diff_type, order_type, time=None):
        """Apply an orderdiff to the orderbook.
        
        Args:
            diff_type: Type of diff. Accepted values are 'create', 'take', 'delete'.
            order_type: Type of diffed order. Accepted values are 'bid', 'ask.
        """
        if order_type == 'bid':
            if diff_type == 'create':
                self.create_bid(price, amount)
            elif diff_type == 'take' or diff_type == 'change':
                self.take_bid(price, amount)
            elif diff_type == 'delete':
                self.delete_bid(price, amount)

        elif order_type == 'ask':
            if diff_type == 'create':
                self.create_ask(price, amount)
            elif diff_type == 'take' or diff_type == 'change':
                self.take_ask(price, amount)
            elif diff_type == 'delete':
                self.delete_ask(price, amount)

        self._time = time or self._time
        self._diff += 1

    def top_bid(self):
        """Returns top bid price."""
        return self._bid_prices[0]

    def top_ask(self):
        """Returns top ask price."""
        return self._ask_prices[0]

    def bids(self, n=10):
        """Returns top n number of bid prices."""
        return self._bid_prices[:n]

    def bid_volume(self, n=10):
        """Returns top n number of bid volumes."""
        return [self._bids[price] for price in self._bid_prices[:n]]

    def bid_order(self, n=10):
        """Returns top n number of bid orders."""
        return [OrderEntry(price, self._bids[price]) for price in self._bid_prices[:n]]

    def asks(self, n=10):
        """Returns top n number of ask prices."""
        return self._ask_prices[:n]

    def ask_volume(self, n=10):
        """Returns top n number of ask volumes."""
        return [self._asks[price] for price in self._ask_prices[:n]]

    def ask_order(self, n=10):
        """Returns top n number of ask orders."""
        return [OrderEntry(price, self._asks[price]) for price in self._ask_prices[:n]]

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

import bisect
from datetime import datetime


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
        """Return mid price."""
        return (self.top_bid() + self.top_ask()) / 2

    def spread(self):
        """Return bid-ask spread."""
        return self.top_ask() - self.top_bid()

    def record_diffs(self, depth=10):
        """Start recording applied diffs and compute time sensative metrics.

        Args:
            depth: number of orders at top of orderbook to keep track of
        """
        self._diffs      = 0
        self._depth      = depth
        self._recording  = True
        self._start_time = self._time

        self._bp_grad = [0 for i in range(depth)]   # bid price gradient
        self._ap_grad = [0 for i in range(depth)]   # ask price gradient
        self._bv_grad = [0 for i in range(depth)]   # bid volume gradient
        self._av_grad = [0 for i in range(depth)]   # ask volume gradient

        self._event_count = {
            'create_ask': 0,
            'create_bid': 0,
            'delete_ask': 0,
            'delete_bid': 0,
            'take_ask': 0,
            'take_bid': 0
        }

    def stop_recording(self):
        """Stop recording diff events."""
        self._recording = False

    def recorded_gradient(self):
        """Return order gradients as (bid price, ask price, bid vol, ask vol)."""
        return self._bid_price_grad, self._ask_price_grad, self._bid_volume_grad, self._ask_volume_grad

    def recorded_events(self):
        """Return count of recorded events."""
        # Only shallow copy is needed
        return self._event_count.copy()

    def _save(self):
        """Cache current top orders at depth from the :py:meth`record_diffs`."""
        self._collision_count = 0
        self._prev_time = self._time
        self._prev_bp   = self.bids(self._depth)          # bid price
        self._prev_ap   = self.asks(self._depth)          # ask price
        self._prev_bv   = self.bid_volume(self._depth)    # bid volume
        self._prev_av   = self.ask_volume(self._depth)    # ask volume

    def _update_record(self, diff_type, order_type):
        """Update recorded metrics."""
        if diff_type == 'change':
            diff_type = 'take'

        event = '_'.join(diff_type, order_type)
        self._event_count[event] += 1

        # Compute orderbook gradients with second resolution.
        if self._prev_time == self._time:
            self._collision_count += 1
        else:
            end_bp  = self.bids(self._depth)
            end_ap  = self.asks(self._depth)
            end_bv  = self.bid_volume(self._depth)
            end_av  = self.ask_volume(self._depth)

            for i in range(self._depth):
                self._bp_grad[i] += (end_bp[i] - self._prev_bp[i]) / self._collision_count
                self._ap_grad[i] += (end_ap[i] - self._prev_ap[i]) / self._collision_count
                self._bv_grad[i] += (end_bv[i] - self._prev_bv[i]) / self._collision_count
                self._av_grad[i] += (end_av[i] - self._prev_av[i]) / self._collision_count

    def apply_diffs_order_gradient(self, diffs, depth=10):
        """Compute gradient from applying diffs. The calling instance will be modified.

        Args:
            diffs: List of dicts with keys conforming to :py:meth:`apply_diff`
            depth: The orderbook depth in returned gradient.

        Returns:
            4 lists, ordered as, bid price gradient, ask price gradient, bid
            volume gradient, ask volume gradient.
        """
        t = diffs.time
        bid_price_grad  = [0 for i in range(depth)]
        ask_price_grad  = [0 for i in range(depth)]
        bid_volume_grad = [0 for i in range(depth)]
        ask_volume_grad = [0 for i in range(depth)]

        for time in t.unique():
            # @Refactor: can just multiple by sum(t==time) in grad calculation
            tdiff = 1 / sum(t == time)

            for i, diff in diffs[t == time].iterrows():
                start_bid_price  = self.bids(depth)
                start_ask_price  = self.asks(depth)
                start_bid_volume = self.bid_volume(depth)
                start_ask_volume = self.ask_volume(depth)

                self.apply_diff(**{**diff, 'time': time+tdiff*i})

                end_bid_price    = self.bids(depth)
                end_ask_price    = self.asks(depth)
                end_bid_volume   = self.bid_volume(depth)
                end_ask_volume   = self.ask_volume(depth)

                for i in range(depth):
                    bid_price_grad[i]  += (end_bid_price[i] - start_bid_price[i]) / tdiff
                    ask_price_grad[i]  += (end_ask_price[i] - start_ask_price[i]) / tdiff
                    bid_volume_grad[i] += (end_bid_volume[i] - start_bid_volume[i]) / tdiff
                    ask_volume_grad[i] += (end_ask_volume[i] - start_ask_volume[i]) / tdiff

        return bid_price_grad, ask_price_grad, bid_volume_grad, ask_volume_grad

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
            price: float for price of changed order
            amount: float for changed order volume
            diff_type: Type of diff. Accepted values are 'create', 'take', 'delete'.
            order_type: Type of diffed order. Accepted values are 'bid', 'ask'.
            time: (optional) time which the diff event happened
        """

        if self._recording:
            self._save()

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

        if self._recording:
            self._update_record(diff_type, order_type)

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
        return [(price, self._bids[price]) for price in self._bid_prices[:n]]

    def asks(self, n=10):
        """Returns top n number of ask prices."""
        return self._ask_prices[:n]

    def ask_volume(self, n=10):
        """Returns top n number of ask volumes."""
        return [self._asks[price] for price in self._ask_prices[:n]]

    def ask_order(self, n=10):
        """Returns top n number of ask orders."""
        return [(price, self._asks[price]) for price in self._ask_prices[:n]]

    @classmethod
    def fromstring(cls, bids, asks, time=-1):
        """Constructor with flexible type.

        Convert all values to float before putting them into internal storage.
        Helpful in dealing with json datasets keyed by string formatted price.
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

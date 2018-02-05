class Metric:
    '''Base class with common functions of single valued metrics'''

    def __int__(self):
        return int(self._value)

    def __float__(self):
        return float(self._value)

    def __neg__(self):
        return -self._value

    def __abs__(self):
        return abs(self._value)

    def __str__(self):
        return str(self._value)

    def __repr__(self):
        return str(self._value)

    def __bool__(self):
        return bool(self._value)

    def __eq__(self, other):
        return self._value == other

    def __ne__(self, other):
        return self._value != other

    def __lt__(self, other):
        return self._value < other

    def __gt__(self, other):
        return self._value > other

    def __le__(self, other):
        return self._value <= other

    def __ge__(self, other):
        return self._value >= other

    def __add__(self, other):
        return self._value + other

    def __sub__(self, other):
        return self._value - other

    def __mul__(self, other):
        return self._value * other

    def __truediv__(self, other):
        return self._value / other

    def __floordiv__(self, other):
        return self._value // other

    def __divmod__(self, other):
        return divmod(self._value, other)

    def __mod__(self, other):
        return self._value % other

    def __pow__(self, other):
        return self._value ** other

    def __radd__(self, other):
        return other + self._value

    def __rsub__(self, other):
        return other - self._value

    def __rmul__(self, other):
        return other * self._value

    def __rtruediv__(self, other):
        return other / self._value

    def __rfloordiv__(self, other):
        return other // self._value

    def __rdivmod__(self, other):
        return divmod(other, self._value)

    def __rmod__(self, other):
        return other % self._value

    def __rpow__(self, other):
        return other ** self._value

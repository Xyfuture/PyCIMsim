class Stime:
    def __init__(self, tick: int, epsilon: int = 0):
        self._tick = tick
        self._epsilon = epsilon

    @property
    def tick(self):
        return self._tick

    @property
    def epsilon(self):
        return self._epsilon

    def __gt__(self, other) -> bool:
        if self._tick == other._tick:
            return self._epsilon > other._epsilon
        return self._tick > other._tick

    def __eq__(self, other) -> bool:
        return self._tick == other._tick and self._epsilon == other._epsilon

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)

    def __lt__(self, other) -> bool:
        if self._tick == other._tick:
            return self._epsilon < other._epsilon
        return self._tick < other._tick

    def __ge__(self, other) -> bool:
        return not self.__lt__(other)

    def __le__(self, other) -> bool:
        return not self.__gt__(other)

    def __add__(self, other):
        if isinstance(other,int):
            return Stime(self._tick + other, self._epsilon)
        elif isinstance(other,tuple):
            return Stime(self._tick + other[0], self._epsilon + other[1])
        return None

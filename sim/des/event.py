from sim.des.stime import Stime


class Event:
    def __init__(self, compo, handler, time: Stime):
        self.compo = compo
        self.handler = handler
        self.time = time

    def process(self):
        assert callable(self.handler)
        self.handler()

    def __eq__(self, other):
        return self.time == other.time

    def __gt__(self, other):
        return self.time > other.time

    def __lt__(self, other):
        return self.time < other.time

    def __ge__(self, other):
        return self.time >= other.time

    def __le__(self, other):
        return self.time <= other.time

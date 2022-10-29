

class event:
    def __init__(self,compo,handler,time):
        self.compo = compo
        self.handler = handler
        self.time = time

    def process(self):
        if callable(self.handler):
            self.handler()
        else:
            raise ("not callable")



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

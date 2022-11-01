
from sim.des.simulator import *
from sim.des.stime import  *
from sim.des.event import *
from sim.des.base_compo import *


class temp(BaseCompo):
    def __init__(self, sim, cnt):
        super().__init__(sim)
        self.sim = sim
        self.cnt = cnt

    def process (self):
        print("time : {} , {}".format(self.sim.current_time._tick, self.sim.current_time._epsilon))
        if self.cnt>0:
            ent = Event(None, self.process, self.sim.next_tick)
            self.sim.add_event(ent)
            tt = Event(None, self.process, self.sim.next_tick)
            self.sim.add_event(tt)
            t = self.sim.current_time + 100
            ent = Event(None, self.process, t)
            self.sim.add_event(ent)
        self.cnt -= 1

    def initialize(self):
        ent = Event(None, self.process, self.sim.next_tick)
        self.sim.add_event(ent)


if __name__ == "__main__":
    sim = Simulator()
    t = temp(sim,5)
    # sim.add_compo(t)
    sim.initialize()

    sim.run()


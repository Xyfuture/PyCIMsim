from sim.core.compo.base_core_compo import BaseCoreCompo
from sim.des.stime import Stime


class PerformanceCounter:
    def __init__(self,compo:BaseCoreCompo):
        self._compo = compo
        self._total_ticks = 0
        self.start_time = Stime(0,0)
        self.trigger = False

    def begin(self):
        self.start_time = self._compo.current_time
        self.trigger = True

    def finish(self):
        if (self.trigger):
            self._total_ticks += (self._compo.current_time.tick-self.start_time.tick)
            self.trigger = False
        else:
            raise "error"

    def get_ticks(self):
        return self._total_ticks

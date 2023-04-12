from sim.core.compo.base_core_compo import BaseCoreCompo
from sim.des.stime import Stime


class BaseCounter:
    def __init__(self, name):
        self.name = name

        self.trigger = False
        self.ticks = 0

        self.start_time = Stime(0, 0)

    def begin(self, ctime: Stime):
        self.start_time = ctime
        self.trigger = True

    def finish(self, ctime: Stime):
        assert self.trigger
        self.ticks += ctime.tick - self.start_time.tick
        self.trigger = False

    def get_ticks(self):
        return self.ticks


class PerformanceCounter:
    def __init__(self, compo: BaseCoreCompo):
        self._compo = compo
        self.total_counter = BaseCounter("total")

        self.counter_map = {}

    def begin(self, name=None):
        ctime = self._compo.current_time
        if name :
            if name not in self.counter_map:
                self.counter_map[name] = BaseCounter(name)

            self.counter_map[name].begin(ctime)

        self.total_counter.begin(ctime)

    def finish(self,name=None):
        ctime = self._compo.current_time
        if name:
            self.counter_map[name].finish(ctime)
        self.total_counter.finish(ctime)

    def get_total_ticks(self):
        return self.total_counter.get_ticks()

    def get_all_ticks(self):
        all_ticks = {"total":self.total_counter.get_ticks()}

        for k,v in self.counter_map.items():
            all_ticks[k] = v.get_ticks()
        return all_ticks

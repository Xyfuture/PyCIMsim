from abc import ABCMeta,abstractmethod
# from simulator import *

class BaseCompo(metaclass=ABCMeta):
    def __init__(self,sim):
        self._sim = sim
        self._sim.add_compo(self)

    @property
    def sim(self):
        return self._sim


    @abstractmethod
    def initialize(self):
        pass


    def add_event(self,ent):
        self._sim.add_event(ent)


    @property
    def current_time(self):
        return self._sim.current_time

    @property
    def next_tick(self):
        return self._sim.next_tick
    @property
    def next_epsilon(self):
        return self._sim.next_epsilon

    @property
    def next_update_epsilon(self):
        return self._sim.next_update_epsilon

    @property
    def next_handle_epsilon(self):
        return self._sim.next_handle_epsilon
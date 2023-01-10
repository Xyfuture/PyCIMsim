from abc import ABCMeta, abstractmethod
# from simulator import *
from sim.des.event import Event
from sim.des.stime import Stime


class BaseCompo(metaclass=ABCMeta):
    def __init__(self, sim, parent_compo=None):
        self._sim = sim
        self._sim.add_compo(self)
        self._parent_compo = parent_compo

    @property
    def sim(self):
        return self._sim

    def initialize(self):
        pass

    def make_event(self, handler, time):
        self._sim.add_event(Event(self, handler, time))

    def add_event(self, ent):
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


def event_handler(func):
    func.last_run_time = Stime(-1, -1)

    def run_func(*args, **kwargs):
        compo: BaseCompo = args[0]
        # 一个tick-epsilon 只能跑一次
        if func.last_run_time != compo.current_time:
            func.last_run_time = compo.current_time
            func(*args, **kwargs)

    return run_func

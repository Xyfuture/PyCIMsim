import queue
from collections import OrderedDict

from sim.des.stime import *
from sim.des.event import *
from sim.des.base_compo import *


class EventWrapper:
    def __init__(self, ent:Event):
        self._event = ent

    def __hash__(self):
        tmp_str = str(self._event.handler) + str(self._event.time.tick) + str(self._event.time.epsilon) + str(self._event.compo)
        return hash(tmp_str)

    def __eq__(self, other):
        return self._event.time == other._event.time and \
               self._event.handler == other._event.handler and\
               self._event.compo == other._event.compo

    def get_event(self):
        return self._event



class Simulator:

    def __init__(self):
        self._ctime = Stime(0, 0)
        self._compos = list()
        self._event_queue = queue.PriorityQueue()

        self._tmp_event_set = OrderedDict()

    def initialize(self):
        for compo in self._compos:
            compo.initialize()
        self.flush_queue_buffer()


    def add_event(self,event_):
        # assert self._ctime != event_.time # 不能插入当前时间的事件
        self._tmp_event_set[EventWrapper(event_)] = None

    def flush_queue_buffer(self):
        for ent in self._tmp_event_set.keys():
            self._event_queue.put(ent.get_event())
        self._tmp_event_set = OrderedDict()

    def run(self):

        while not self._event_queue.empty():
            tmp_event = self._event_queue.get()
            self._ctime = tmp_event.time

            tmp_event.process()

            if not self._event_queue.empty():
                if self._ctime != self._event_queue.queue[0].time:
                    self.flush_queue_buffer()
            else:
                self.flush_queue_buffer()


    def add_compo(self, compo:BaseCompo):
        if isinstance(compo, BaseCompo):
            self._compos.append(compo)

    @property
    def current_time(self):
        return self._ctime

    @property
    def next_tick(self):
        return Stime(self._ctime.tick + 1,0)

    @property
    def next_epsilon(self):
        return self._ctime + (0, 1)

    @property
    def next_update_epsilon(self):
        if self._ctime.epsilon % 2 == 0:
            return self._ctime + (0,2)
        return self._ctime + (0,1)

    @property
    def next_handle_epsilon(self):
        if self._ctime.epsilon % 2 == 0:
            return self._ctime + (0,1)
        return self._ctime + (0,2)
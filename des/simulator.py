import queue

from des.event import *
from des.stime import *
from des.base_compo import *


class event_wrapper:
    def __init__(self,ent:event):
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



class simulator:

    def __init__(self):
        self._ctime = stime(0, 0)
        self._compos = list()
        self._event_queue = queue.PriorityQueue()

        self._tmp_event_set = set()

    def initialize(self):
        for compo in self._compos:
            compo.initialize()
        self.flush_queue_buffer()


    def add_event(self,event_):
        self._tmp_event_set.add(event_wrapper(event_))

    def flush_queue_buffer(self):
        for ent in self._tmp_event_set:
            self._event_queue.put(ent.get_event())
        self._tmp_event_set = set()

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


    def add_compo(self,compo:base_compo):
        if isinstance(compo,base_compo):
            self._compos.append(compo)

    @property
    def current_time(self):
        return self._ctime

    @property
    def next_tick(self):
        return self._ctime + 1

    @property
    def next_epsilon(self):
        return self._ctime + (0, 1)

    @property
    def next_update_epslion(self):
        if self._ctime.epsilon % 2 == 0:
            return self._ctime + (0,2)
        return self._ctime + (0,1)

    @property
    def next_handle_epsilon(self):
        if self._ctime.epsilon % 2 == 0:
            return self._ctime + (0,1)
        return self._ctime + (0,2)
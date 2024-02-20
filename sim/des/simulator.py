import heapq
from collections import OrderedDict
from ordered_set import OrderedSet
import time

from sim.des.stime import *
from sim.des.event import *
from sim.des.base_compo import *


class EventWrapper:
    def __init__(self, ent: Event):
        self._event = ent

    def __hash__(self):
        tmp_str = id(self._event.handler) + self._event.time.tick + self._event.time.epsilon
        return hash(tmp_str)

    def __eq__(self, other):
        return self._event.time == other._event.time and \
            self._event.handler == other._event.handler and \
            self._event.compo == other._event.compo

    def get_event(self):
        return self._event


class PriorityQueue:
    def __init__(self):
        self._list = []

    def top(self):
        return self._list[0]

    def get(self):
        return heapq.heappop(self._list)

    def put(self, item):
        heapq.heappush(self._list, item)

    def empty(self):
        return len(self._list) == 0

    def __len__(self):
        return len(self._list)

    def size(self):
        return len(self._list)


class Simulator:

    def __init__(self):
        self._ctime = Stime(0, 0)
        self._compos = []
        self._event_queue = PriorityQueue()

        # self._tmp_event_set = set()
        self._queue_buffer_set = OrderedSet()
        self._event_cnt = 0

    def initialize(self):
        for compo in self._compos:
            compo.initialize()
        self.flush_queue_buffer()

    def add_event(self, event_):
        assert self._ctime < event_.time  # 不能插入当前时间的事件
        self._queue_buffer_set.add(EventWrapper(event_))

    def flush_queue_buffer(self):
        for ent in self._queue_buffer_set:
            self._event_queue.put(ent.get_event())
        # self._tmp_event_set = set()
        self._queue_buffer_set = OrderedSet()

    def run(self):
        # in heapq more fast
        st = time.time()
        while not self._event_queue.empty():
            cur_event = self._event_queue.get()
            assert self._ctime <= cur_event.time

            self._ctime = cur_event.time

            cur_event.process()

            if not self._event_queue.empty():
                if self._ctime != self._event_queue.top().time:
                    self.flush_queue_buffer()
            else:
                self.flush_queue_buffer()

            self._event_cnt += 1

            if __debug__:
                self.get_process()

        ed = time.time()
        print(f"run simulate time {self.current_time}")
        print(f"run time {ed - st} seconds")

    def add_compo(self, compo: BaseCompo):
        assert isinstance(compo, BaseCompo)
        self._compos.append(compo)

    def get_process(self,interval=0):
        if interval and self._event_cnt % interval:
            print(f"Simulator> Event Cnt:{self._event_cnt}")


    @property
    def current_time(self):
        return self._ctime

    @property
    def next_tick(self):
        return Stime(self._ctime.tick + 1, 0)

    @property
    def next_epsilon(self):
        return self._ctime + (0, 1)

    @property
    def next_update_epsilon(self):
        if self._ctime.epsilon % 2 == 0:
            return self._ctime + (0, 2)
        return self._ctime + (0, 1)

    @property
    def next_handle_epsilon(self):
        if self._ctime.epsilon % 2 == 0:
            return self._ctime + (0, 1)
        return self._ctime + (0, 2)

    @property
    def event_cnt(self):
        return self._event_cnt

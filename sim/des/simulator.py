import heapq
from collections import OrderedDict
import time

from sim.des.stime import *
from sim.des.event import *
from sim.des.base_compo import *


class EventWrapper:
    def __init__(self, ent: Event):
        self._event = ent

    def __hash__(self):
        # tmp_str = str(self._event.handler) + str(self._event.time.tick) + str(self._event.time.epsilon) + str(
        # self._event.compo)
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
        return heapq.nsmallest(1, self._list)[0]

    def get(self):
        return heapq.heappop(self._list)

    def put(self, item):
        heapq.heappush(self._list, item)

    def merge_list(self, list_):
        heapq.heapify(list_)
        self._list = list(heapq.merge(self._list, list_))

    def empty(self):
        return len(self._list) == 0

    def __len__(self):
        return len(self._list)

    def size(self):
        return len(self._list)


class Simulator:

    def __init__(self):
        self._ctime = Stime(0, 0)
        self._compos = list()
        self._event_queue = PriorityQueue()

        self._tmp_event_set = set()
        self._event_cnt = 0

    def initialize(self):
        for compo in self._compos:
            compo.initialize()
        self.flush_queue_buffer()

    def add_event(self, event_):
        # assert self._ctime != event_.time # 不能插入当前时间的事件
        self._tmp_event_set.add(EventWrapper(event_))

    def flush_queue_buffer(self):
        tmp_list = []
        for ent in self._tmp_event_set:
            tmp_list.append(ent.get_event())
        self._event_queue.merge_list(tmp_list)
        self._tmp_event_set = set()

    def run(self):
        # in heapq more fast
        st = time.time()
        while not self._event_queue.empty():
            cur_event = self._event_queue.get()
            self._ctime = cur_event.time

            cur_event.process()

            if not self._event_queue.empty():
                if self._ctime != self._event_queue.top().time:
                    self.flush_queue_buffer()
            else:
                self.flush_queue_buffer()

            self._event_cnt += 1

            # if __debug__:
            #     if self._event_cnt % 1000 == 0:
            #         print(f"event cnt:{self._event_cnt}")
        ed = time.time()
        print(f"run simulate time {self.current_time}")
        print(f"run time {ed - st}")

    def new_run(self):
        self._ctime = Stime(-1, -1)
        st = time.time()
        while not self._event_queue.empty():

            if self._ctime == self._event_queue.top().time:
                assert False
            else:
                self._ctime = self._event_queue.top().time

            for i in range(self._event_queue.size()):
                if self._ctime != self._event_queue.top().time:
                    break
                cur_event = self._event_queue.get()
                cur_event.process()
                self._event_cnt += 1

            self.flush_queue_buffer()
        ed = time.time()
        print(f"run simulate time {self.current_time}")
        print(f"run time {ed - st}")

    def add_compo(self, compo: BaseCompo):
        if isinstance(compo, BaseCompo):
            self._compos.append(compo)

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

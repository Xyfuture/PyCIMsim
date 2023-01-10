from sim.des.base_compo import BaseCompo
from sim.des.stime import Stime
from sim.des.utils import fl


class Trigger(BaseCompo):
    """
    用于衔接电路级模拟和行为级模拟，不同于register的设计了
    """

    def __init__(self, sim, compo):
        super(Trigger, self).__init__(sim, compo)

        self._status = False  # 为 True及触发

        self._next_run_time = Stime(0, 0)

        self._callbacks = fl()

    def pulse(self):
        if self._status:
            self.make_event(self._callbacks, self.next_handle_epsilon)
            self._status = False

    def set(self):
        self._status = True
        self.run_next()

    def unset(self):
        self._status = False
        # 下个周期不用跑

    def run_next(self):
        if not self.is_run_next():
            next_time = self.next_tick
            self.make_event(self.pulse, next_time)

            self._next_run_time = next_time

    def is_run_next(self) -> bool:
        next_time = self.next_tick
        if self._next_run_time == next_time:
            return True
        return False

    def add_callback(self, func):
        self._callbacks.add_func(func)

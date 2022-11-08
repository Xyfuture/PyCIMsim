from sim.core.utils.port.uni_port import UniWritePort, UniReadPort
from sim.core.utils.register.base_register import BaseRegister
from sim.des.base_compo import BaseCompo
from sim.des.event import Event
from sim.des.stime import Stime
from sim.des.base_element import BaseElement


class RegEnable(BaseRegister):
    def __init__(self, compo: BaseCompo, callback):
        super(RegEnable, self).__init__(compo)

        self._payload = None
        self._update_time = None

        self._enable_port = None
        self._payload_port = None

        self._callback = callback

        self._next_run_time = Stime(0, 0)

    def init_ports(self):
        self._enable_port = UniReadPort(self._compo, self.process_enable)
        self._payload_port = UniReadPort(self._compo, None)

        return self._enable_port, self._payload_port

    def initialize(self, payload):
        self._payload = payload
        self._update_time = self.current_time

    def pulse(self):
        cur_time = self.current_time
        if self._enable_port.read(cur_time):
            self._payload = self._payload_port.read(cur_time)
            self._update_time = cur_time

            self.run_next()

            if callable(self._callback):
                # self._callback()
                self.make_event(self._callback, self.next_handle_epsilon)

    def process_enable(self):
        if self._enable_port.read(self.current_time):
            self.run_next()

    def run_next(self):
        if not self.is_run_next():
            next_time = self.next_tick
            # event = Event(self._compo, self.pulse, next_time)
            # self._compo.add_event(event)
            self.make_event(self.pulse, next_time)

            self._next_run_time = next_time

    def is_run_next(self) -> bool:
        next_time = self.next_tick
        if self._next_run_time == next_time:
            return True
        return False

    def read(self, time=None):
        if time:
            if self._update_time.tick == time.tick:
                return self._payload
            return None
        return self._payload

class RegNext(BaseRegister):
    def __init__(self, compo, callback):
        super(RegNext, self).__init__(compo)

        self._callback = callback

        self._next_payload = None  # 下一个更新时应该保存的值
        self._payload = None
        self._update_time = None

        # self._payload_port = None

        self._next_run_time = Stime(0, 0)

    def initialize(self, payload):
        self._payload = payload
        self._update_time = self.current_time

    def pulse(self):
        self._payload = self._next_payload
        self._update_time = self.current_time

        if callable(self._callback):
            self._callback()

    def write(self, payload):
        self._next_payload = payload

        next_time = self.next_tick
        if next_time == self._next_run_time:
            return

        self.make_event(self.pulse, next_time)
        self._next_run_time = next_time

    def read(self, time=None):
        if time:
            if self._update_time.tick == time.tick:
                return self._payload
            return None
        return self._payload

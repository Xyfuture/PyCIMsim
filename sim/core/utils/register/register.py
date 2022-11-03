from sim.core.utils.port.uni_port import UniWritePort, UniReadPort
from sim.des.base_compo import BaseCompo
from sim.des.event import Event
from sim.des.stime import Stime


class RegEnable:
    def __init__(self, compo, callback: BaseCompo):
        self._compo: BaseCompo = compo

        self._payload = None
        self._update_time = None

        self._enable_port = None
        self._payload_port = None

        self._callback = None

        self._next_run_time = None

    def init_ports(self):
        self._enable_port = UniReadPort(self._compo, self.process_enable)
        self._payload_port = UniReadPort(self._compo, None)

        return self._enable_port, self._payload_port

    def pulse(self):
        cur_time = self._compo.current_time
        if self._enable_port.read(cur_time):
            self._payload = self._payload_port.read(cur_time)
            self._update_time = cur_time

            self.run_next()

            if callable(self._callback):
                self._callback()

    def process_enable(self):
        if self._enable_port.read(self._compo.current_time):
            self.run_next()

    def run_next(self):
        if not self.is_run_next():
            next_time = Stime(self._compo.current_time.tick, 0)
            event = Event(self._compo, self.pulse, next_time)
            self._compo.add_event(event)

            self._next_run_time = next_time

    def is_run_next(self) -> bool:
        next_time = Stime(self._compo.current_time.tick, 0)
        if self._next_run_time == next_time:
            return True
        return False

from __future__ import annotations

from sim.circuit.port.channel import UniChannel
from sim.circuit.register.base_register import BaseRegister
from sim.circuit.port.port import UniReadPort, UniWritePort, UniPulseReadPort, UniPulseWritePort
from sim.des.base_compo import BaseCompo
from sim.des.stime import Stime
from sim.des.utils import fl


class RegNext(BaseRegister):
    def __init__(self, compo):
        super(RegNext, self).__init__(compo)

        self._payload = None
        self._update_time = None

        self._next_run_time = Stime(0, 0)

        self._input_read_port = UniReadPort(compo)
        self._input_read_port.add_callback(self.process_input)
        self._output_write_port = UniWritePort(compo)

        self._input_write_port = None
        self._output_read_port = None

    def initialize(self, payload):
        self._payload = payload
        self._update_time = self.current_time

        self._output_write_port.write(self._payload)

    def pulse(self):
        if self._input_read_port.read() != self._payload:
            self._update_time = self.current_time
            self._payload = self._input_read_port.read()

            self._output_write_port.write(self._payload)

    def process_input(self):
        if self._input_read_port.read() != self._payload:
            self.run_next()

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

    def get_input_read_port(self):
        return self._input_read_port

    def get_input_write_port(self):
        self._input_write_port = UniWritePort(self._compo)
        self._input_write_port // self._input_read_port

        return self._input_write_port

    def get_output_read_port(self):
        self._output_read_port = UniReadPort(self._compo)
        self._output_write_port // self._output_read_port

        return self._output_read_port

    def get_output_write_port(self):
        return self._output_write_port


class RegEnable(BaseRegister):
    def __init__(self, compo: BaseCompo):
        super(RegEnable, self).__init__(compo)

        self._payload = None
        self._update_time = None

        self._next_run_time = Stime(0, 0)

        self._input_read_port = UniReadPort(compo)
        self._input_read_port.add_callback(self.process_input)
        self._output_write_port = UniWritePort(compo)

        self._enable_read_port = UniReadPort(compo)
        self._enable_read_port.add_callback(self.process_enable)

        self._enable_write_port = None
        self._output_read_port = None
        self._input_write_port = None

    def initialize(self, payload):
        self._payload = payload
        self._update_time = self.current_time

    def pulse(self):
        if self._enable_read_port.read():
            if self._input_read_port.read() != self._payload:
                self._payload = self._input_read_port.read()
                self._update_time = self.current_time

                self._output_write_port.write(self._payload)

    def process_input(self):
        if self._input_read_port.read() != self._payload:
            self.run_next()

    def process_enable(self):
        if self._enable_read_port.read():
            self.run_next()

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

    def get_input_read_port(self):
        return self._input_read_port

    def get_input_write_port(self):
        self._input_write_port = UniWritePort(self._compo)
        self._input_write_port // self._input_read_port

        return self._input_write_port

    def get_output_read_port(self):
        self._output_read_port = UniReadPort(self._compo)
        self._output_write_port // self._output_read_port

        return self._output_read_port

    def get_output_write_port(self):
        return self._output_write_port

    def get_enable_read_port(self):
        return self._enable_read_port

    def get_enable_write_port(self):
        self._enable_write_port = UniWritePort(self._compo)
        self._enable_write_port // self._enable_read_port

        return self._enable_write_port


class Trigger(BaseRegister):
    def __init__(self,compo):
        super(Trigger, self).__init__(compo)
        self._next_status = False

        self._payload = None
        self._update_time = None

        self._next_run_time = Stime(0,0)

        self._input_read_port = UniPulseReadPort(compo)
        self._input_read_port.add_callback(self.process_input)

        self._input_write_port = None

        self._callbacks = fl()

    def pulse(self):
        if self._payload:
            self.make_event(self._callbacks,self.next_handle_epsilon)

    def process_input(self):
        self._payload = self._input_read_port.read()
        self.next_tick()

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

    def add_callback(self,func):
        self._callbacks.add_func(func)

    def get_input_read_port(self):
        return self._input_read_port

    def get_input_write_port(self):
        self._input_write_port = UniPulseWritePort(self._compo)
        self._input_write_port // self._input_read_port
        return self._input_write_port


from __future__ import annotations

from sim.circuit.register.base_register import BaseRegister
from sim.circuit.wire.base_wire import BaseWire
from sim.circuit.wire.wire import UniReadWire, UniWriteWire
from sim.des.base_compo import BaseCompo
from sim.des.event import Event
from sim.des.base_element import BaseElement
from sim.des.stime import Stime
from sim.des.utils import fl


class RegNext(BaseRegister):
    def __init__(self, compo):
        super(RegNext, self).__init__(compo)

        self._payload = None
        self._update_time = None

        self._next_run_time = Stime(0, 0)

        self._in_wire = UniReadWire(compo)
        self._in_wire.add_callback(self.process_input)

        self._out_wire_write_port = UniWriteWire(compo)
        self._out_wire_read_port = UniReadWire(compo)
        self._out_wire_write_port // self._out_wire_read_port

    def initialize(self, payload):
        self._payload = payload
        self._update_time = self.current_time

    def get_wires(self):
        return self._in_wire,self._out_wire_read_port

    def pulse(self):
        if self._in_wire.read() != self._payload:
            self._update_time = self.current_time
            self._payload = self._in_wire.read()

            self._out_wire_write_port.write(self._payload)

    def process_input(self):
        if self._in_wire.read() != self._payload:
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


class RegEnable(BaseRegister):
    def __init__(self, compo: BaseCompo, callback):
        super(RegEnable, self).__init__(compo)

        self._payload = None
        self._update_time = None

        self._next_run_time = Stime(0, 0)

        self._in_payload_wire = UniReadWire(compo)
        self._in_payload_wire.add_callback(self.process_input)

        self._in_enable_wire = UniReadWire(compo)
        self._in_enable_wire.add_callback(self.process_enable)

        self._out_wire_write_port = UniWriteWire(compo)
        self._out_wire_read_port = UniReadWire(compo)
        self._out_wire_write_port // self._out_wire_read_port


    def get_wires(self):
        return self._in_enable_wire,self._in_payload_wire,self._out_wire_read_port

    def initialize(self, payload):
        self._payload = payload
        self._update_time = self.current_time

    def pulse(self):
        if self._in_enable_wire.read():
            if self._in_payload_wire.read() != self._payload:
                self._payload = self._in_payload_wire.read()
                self._update_time = self.current_time

                self._out_wire_write_port.write(self._payload)

    def process_input(self):
        if self._in_payload_wire.read() != self._payload:
            self.run_next()

    def process_enable(self):
        if self._in_enable_wire.read():
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



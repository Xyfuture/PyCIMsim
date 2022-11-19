from __future__ import annotations

from sim.circuit.port.port import UniPulseReadPort, UniPulseWritePort, UniReadPort, UniWritePort
from sim.circuit.wire.base_wire import BaseWire
from sim.des.event import Event
from sim.des.simulator import Simulator
from sim.des.stime import Stime
from sim.des.utils import fl


class UniChannel:
    def __init__(self, wire):
        self._wire = wire

        self._payload = None
        self._next_payload = None

        self._sim:Simulator = self._wire._sim

    def read_value(self):
        return self._payload

    def write_value(self,payload):
        self._next_payload = payload
        self._sim.add_event(Event(None,self.update_value,self._sim.next_update_epsilon))

    def update_value(self):
        if self._next_payload != self._payload:
            self._payload = self._next_payload

            self._sim.add_event(Event(None, self._wire.channel_callback, self._sim.next_handle_epsilon))

class UniPulseChannel(UniChannel):
    def __init__(self,wire):
        super(UniPulseChannel, self).__init__(wire)

        self._update_time = Stime(0,0)

        self._next_run_time = Stime(0,0)

    def read_value(self):
        return self._payload

    def update_value(self):
        if self._next_payload != self._payload:
            self._payload = self._next_payload
            self._update_time = self._sim.current_time
            self._sim.add_event(Event(None, self._wire.channel_callback, self._sim.next_handle_epsilon))

            self.run_next()

    def set_to_default(self):
        if self._update_time.tick != self._sim.current_time.tick:
            self._payload = None
            self._update_time = self._sim.current_time
            self._sim.add_event(Event(None, self._wire.channel_callback, self._sim.next_handle_epsilon))

    def run_next(self):
        if not self.is_run_next():
            self._sim.add_event(Event(None,self.set_to_default,self._sim.next_tick))
            self._next_run_time = self._sim.next_tick

    def is_run_next(self) -> bool:
        next_time = self._sim.next_tick
        if self._next_run_time == next_time:
            return True
        return False


class UniWire(BaseWire):
    def __init__(self, compo,as_input=True,as_output=True):
        super(UniWire, self).__init__(compo)

        self._channel = UniChannel(self)
        self._callbacks = fl()

        self._as_input = as_input
        self._as_output = as_output

    def write(self, payload):
        if self._as_output:
            self._channel.write_value(payload)

    def read(self):
        if self._as_input:
            return self._channel.read_value()

    def add_callback(self, *args):
        self._callbacks.add_func(*args)

    def force_read(self):
        return self._channel.read_value()

    def force_write(self, payload):
        return self._channel.write_value(payload)

    def channel_callback(self):
        self._callbacks()

    def __rshift__(self, other:UniWire):
        if isinstance(other, BaseWire):
            self.add_callback(lambda: other.force_write(self.force_read()))
        else:
            raise "error"

    def __lshift__(self, other:UniWire):
        if isinstance(other,BaseWire):
            other.add_callback(lambda: self.force_write(other.force_read()))
        else:
            raise "error"

    @property
    def as_input(self):
        return self._as_input

    @property
    def as_output(self):
        return self._as_output

    @property
    def as_io_wire(self):
        return self._as_input ^ self._as_output


class UniPulseWire(UniWire):
    def __init__(self, compo,as_input=True,as_output=True):
        super(UniPulseWire, self).__init__(compo,as_input,as_output)

        self._channel = UniPulseChannel(self)



def InWire(wire_class,compo):
    return wire_class(compo,as_input=True,as_output=False)

def OutWire(wire_class,compo):
    return wire_class(compo,as_input=False,as_output=True)


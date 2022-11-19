from __future__ import annotations

from sim.circuit.port.port import UniPulseReadPort, UniPulseWritePort, UniReadPort, UniWritePort
from sim.circuit.wire.base_wire import BaseWire


class UniWire(BaseWire):
    def __init__(self, compo,as_input=True,as_output=True):
        super(UniWire, self).__init__(compo)

        self._read = UniReadPort(compo)
        self._write = UniWritePort(compo)

        self._read // self._write

        self._as_input = as_input
        self._as_output = as_output

    def write(self, payload):
        if self._as_output:
            self._write.write(payload)

    def read(self):
        if self._as_input:
            return self._read.read()

    def add_callback(self, *args):
        self._read.add_callback(*args)

    def inner_read(self):
        return self._read.read()

    def inner_write(self,payload):
        return self._write.write(payload)

    def __rshift__(self, other:UniWire):
        if isinstance(other, BaseWire):
            self.add_callback(lambda: other.inner_write(self.inner_read()))
        else:
            raise "error"

    def __lshift__(self, other:UniWire):
        if isinstance(other,BaseWire):
            other.add_callback(lambda: self.inner_write(other.inner_read()))
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

        self._read = UniPulseReadPort(compo)
        self._write = UniPulseWritePort(compo)

        self._read // self._write

        self._as_input = as_input
        self._as_output = as_output


def InWire(wire_class,compo):
    return wire_class(compo,as_input=True,as_output=False)

def OutWire(wire_class,compo):
    return wire_class(compo,as_input=False,as_output=True)


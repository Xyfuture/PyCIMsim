from __future__ import annotations

from sim.circuit.wire.base_wire import BaseWire
from sim.des.base_compo import BaseCompo
from sim.des.event import Event
from sim.des.base_element import BaseElement
from sim.des.stime import Stime
from sim.des.utils import fl


class UniChannel:
    def __init__(self, read_wire: UniReadWire, write_wire: UniWriteWire):
        self._read_wire = read_wire
        self._write_wire = write_wire

        self._read_wire.set_channel(self)
        self._write_wire.set_channel(self)

        self._payload = None
        # self._time = Stime(0, 0)

        self._next_payload = None

    def read_value(self):
        return self._payload

    def write_value(self,payload):
        self._next_payload = payload
        self._write_wire.update_channel()

    def update_value(self):
        if self._next_payload != self._payload:
            self._payload = self._next_payload
            # self._next_payload = None
            self._read_wire.callback()


class UniReadWire(BaseWire):
    def __init__(self, compo: BaseCompo):
        super().__init__(compo)

        self._channel: UniChannel = None
        self._callback = fl()

    def read(self):
        if self._channel:
            return self._channel.read_value()
        return None

    def callback(self):
        if callable(self._callback):
            self.make_event(self._callback, self.next_handle_epsilon)

    def add_callback(self, *args):
        self._callback.add_func(args)

    def set_channel(self, channel):
        self._channel = channel

    def __floordiv__(self, other):
        connect_uni_write(self, other)


class UniWriteWire(BaseWire):
    def __init__(self, compo: BaseCompo):
        super().__init__(compo)

        self._channel: UniChannel = None

    def write(self, payload):
        if self._channel:
            self._channel.write_value(payload)

    def update_channel(self):
        # 这个设计有点烂
        self.make_event(self._channel.update_value,self.next_update_epslion)

    def set_channel(self, channel):
        self._channel = channel

    def __floordiv__(self, other):
        connect_uni_write(self, other)


class UniWire(BaseWire):
    def __init__(self,compo):
        super(UniWire, self).__init__(compo)

        self._read = UniReadWire(compo)
        self._write = UniWriteWire(compo)

        self._read // self._write

    def write(self,payload):
        self._write.write(payload)

    def read(self):
        return self._read.read()

    def add_callback(self,*args):
        self._read.add_callback(args)







def connect_uni_write(port_a, port_b):
    if isinstance(port_a, UniReadWire) and isinstance(port_b, UniWriteWire):
        read_port = port_a
        write_port = port_b
    elif isinstance(port_b, UniReadWire) and isinstance(port_a, UniWriteWire):
        read_port = port_b
        write_port = port_a
    else:
        raise ("wrong port type")

    tmp = UniChannel(read_port, write_port)


# def make_bind_ports(compo,callback):
#     read_port = UniReadPort(compo,callback)
#     write_port = UniWritePort(compo)
#
#     read_port // write_port
#
#     return read_port,write_port

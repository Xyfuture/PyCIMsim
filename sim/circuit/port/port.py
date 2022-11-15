from __future__ import annotations

from sim.circuit.port.channel import UniChannel, connect_with_uni_channel
from sim.circuit.port.base_port import BasePort
from sim.des.base_compo import BaseCompo
from sim.des.utils import fl





class UniReadPort(BasePort):
    def __init__(self, compo: BaseCompo):
        super().__init__(compo)

        self._channel: UniChannel = None
        self._callback = fl()

    def read(self):
        if self._channel:
            return self._channel.read_value()
        return None

    def channel_callback(self):
        if callable(self._callback):
            self.make_event(self._callback, self.next_handle_epsilon)

    def add_callback(self, *args):
        self._callback.add_func(*args)

    def set_channel(self, channel):
        self._channel = channel

    def __floordiv__(self, other):
        connect_with_uni_channel(self, other)

    @property
    def as_read_port(self):
        if self._channel:
            return False
        return True

    @property
    def as_write_port(self):
        return False


class UniWritePort(BasePort):
    def __init__(self, compo: BaseCompo):
        super().__init__(compo)

        self._channel: UniChannel = None

    def write(self, payload):
        if self._channel:
            self._channel.write_value(payload)

    def set_channel(self, channel):
        self._channel = channel

    def __floordiv__(self, other):
        connect_with_uni_channel(self, other)

    @property
    def as_read_port(self):
        return False

    @property
    def as_write_port(self):
        if self._channel:
            return False
        return True


# 内部的线还需要设计一下
class UniWire(BasePort):
    def __init__(self,compo):
        super(UniWire, self).__init__(compo)

        self._read = UniReadPort(compo)
        self._write = UniWritePort(compo)

        self._read // self._write

    def write(self,payload):
        self._write.write(payload)

    def read(self):
        return self._read.read()

    def add_callback(self,*args):
        self._read.add_callback(*args)

    @property
    def as_read_port(self):
        return False

    @property
    def as_write_port(self):
        return False







def connect_uni_write(port_a, port_b):
    if isinstance(port_a, UniReadPort) and isinstance(port_b, UniWritePort):
        read_port = port_a
        write_port = port_b
    elif isinstance(port_b, UniReadPort) and isinstance(port_a, UniWritePort):
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

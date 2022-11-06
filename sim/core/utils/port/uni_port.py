from __future__ import annotations

from sim.core.utils.port.base_port import BasePort
from sim.des.base_compo import BaseCompo
from sim.des.event import Event
from sim.des.base_element import BaseElement


class UniChannel:
    def __init__(self, read_port:UniReadPort, write_port:UniWritePort):
        self._read_port = read_port
        self._write_port = write_port

        self._read_port.set_channel(self)
        self._write_port.set_channel(self)

        self._payload = None
        self._time = None

    # def wirte(self,payload,time):
    #     pass

    def read_value(self, time=None):
        # if time >= self._time:
        #     return self._payload
        # return None
        # 检测是否是同一个cycle,或者不管时间的限制
        if time:
            if time.tick == self._time.tick:
                return self._payload
            # 用于一些同步操作
            return None
        return self._payload


    def update_value(self, payload, time):
        self._payload = payload
        self._time = time

        self._read_port.callback()


class UniReadPort(BasePort):
    def __init__(self, compo: BaseCompo, callback):
        super().__init__(compo)

        self._channel: UniChannel = None
        self._callback = callback

    def read(self, time=None):
        if self._channel:
            return self._channel.read_value(time)
        return None

    def callback(self):
        if callable(self._callback):
            self.make_event(self._callback, self.next_handle_epsilon)

    def set_channel(self, channel):
        self._channel = channel

    def __floordiv__(self, other):
        connect_uni_port(self, other)


class UniWritePort(BasePort):
    def __init__(self, compo: BaseCompo):
        super().__init__(compo)

        self._channel: UniChannel = None

    def write(self, payload, time):
        if self._channel:
            f = lambda: self._channel.update_value(payload, time)
            self.make_event(f, time)

    def set_channel(self, channel):
        self._channel = channel

    def __floordiv__(self, other):
        connect_uni_port(self, other)


def connect_uni_port(port_a, port_b):
    if isinstance(port_a, UniReadPort) and isinstance(port_b, UniWritePort):
        read_port = port_a
        write_port = port_b
    elif isinstance(port_b, UniReadPort) and isinstance(port_a, UniWritePort):
        read_port = port_b
        write_port = port_a
    else:
        raise ("wrong port type")

    tmp = UniChannel(read_port, write_port)


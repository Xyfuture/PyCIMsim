from __future__ import annotations

from sim.des.base_compo import BaseCompo
from sim.des.base_element import BaseElement
from sim.core.utils.port.base_port import BasePort
from sim.core.utils.port.uni_port import UniChannel, UniReadPort, UniWritePort


class BiChannel():
    def __init__(self, left_port: BiPort, right_port: BiPort):
        self._left_port = left_port
        self._right_port = right_port

        self._left_port.set_channel(self, True)
        self._right_port.set_channel(self, False)

        # 左边向右边写
        self._left_to_right_channel = UniChannel(
            self._right_port.read_port, self._left_port.write_port)

        # 右边向左边写
        self._right_to_left_channel = UniChannel(
            self._left_port.read_port, self._right_port.write_port)

    def read_value(self, is_left: bool, time):
        if is_left:
            return self._right_to_left_channel.read_value(time)
        else:
            return self._left_to_right_channel.read_value(time)

    def update_value(self, is_left: bool, payload, time):
        if is_left:
            self._left_to_right_channel.update_value(payload, time)
        else:
            self._right_to_left_channel.update_value(payload, time)


class BiPort(BasePort):
    def __init__(self, compo: BaseCompo, callback):
        super(BiPort, self).__init__(compo)

        self._channel: BiChannel = None

        self._is_left = True

        self._read_port = UniReadPort(compo, callback)
        self._write_port = UniWritePort(compo)

    @property
    def read_port(self):
        return self._read_port

    @property
    def write_port(self):
        return self._write_port

    def set_channel(self, channel, is_left):
        self._channel = channel
        self._is_left = is_left

    def read(self, time=None):
        if self._channel:
            return self._channel.read_value(self._is_left, time)
        return None

    def write(self, payload, time):
        if self._channel:
            f = lambda: self._channel.update_value(self._is_left, payload, time)
            self.make_event(f, time)

    def __floordiv__(self, other):
        connect_bi_port(self, other)


def connect_bi_port(port_a: BiPort, port_b: BiPort):
    left_port = port_a
    right_port = port_b

    tmp = BiChannel(left_port, right_port)

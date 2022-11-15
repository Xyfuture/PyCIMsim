from sim.des.event import Event
from sim.des.simulator import Simulator


# port 是能读写的基本单位, port 和 reg 都是基于port的


class UniChannel:
    def __init__(self, read_port, write_port):
        self._read_port = read_port
        self._write_port = write_port

        self._read_port.set_channel(self)
        self._write_port.set_channel(self)

        self._payload = None

        self._next_payload = None

        self._sim:Simulator = self._read_port._sim

    def read_value(self):
        return self._payload

    def write_value(self,payload):
        self._next_payload = payload
        self._sim.add_event(Event(None,self.update_value,self._sim.next_update_epsilon))

    def update_value(self):
        if self._next_payload != self._payload:
            self._payload = self._next_payload

            self._sim.add_event(Event(None, self._read_port.channel_callback, self._sim.next_handle_epsilon))


def connect_with_uni_channel(port_a, port_b):
    if port_a.as_read_port and port_b.as_write_port:
        read_port = port_a
        write_port = port_b
    elif port_a.as_write_port and port_b.as_read_port:
        read_port = port_b
        write_port = port_a
    else:
        raise "Error"

    tmp = UniChannel(read_port, write_port)


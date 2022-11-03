from sim.des.base_compo import BaseCompo
from sim.des.event import Event

class UniChannel:
    def __init__(self,read_port,write_port):
        self._read_port = read_port
        self._write_port = write_port

        self._payload = None
        self._time = None

    # def wirte(self,payload,time):
    #     pass

    def read_value(self,time):
        if time >= self._time:
            return self._payload
        return None

    def update_value(self,payload,time):
        self._payload = payload
        self._time = time

        self._read_port.callback()


class UniReadPort:
    def __init__(self, compo:BaseCompo, callback):
        self._compo = compo
        self._channel:UniChannel = None
        self._callback = callback

    def read(self,time):
        return self._channel.read_value(time)

    def callback(self):
        if callable(self._callback):
            next_time = self._compo.next_handle_epsilon
            ent = Event(self._compo, self._callback, next_time)
            self._compo.add_event(ent)

    def set_channel(self,channel):
        self._channel = channel


class UniWritePort:
    def __init__(self, compo:BaseCompo):
        self._compo = compo
        self._channel:UniChannel = None

    def write(self,payload,time):
        f = lambda :self._channel.update_value(payload,time)
        ent = Event(self._compo, f, time)
        self._compo.add_event(ent)

    def set_channel(self,channel):
        self._channel = channel



def connect_uni_port(port_a,port_b):
    if isinstance(port_a, UniReadPort) and isinstance(port_b, UniWritePort):
        read_port = port_a
        write_port = port_b
    elif  isinstance(port_b, UniReadPort) and isinstance(port_a, UniWritePort):
        read_port = port_b
        write_port = port_a
    else:
        raise ("wrong port type")

    tmp = UniChannel(read_port, write_port)

    port_a.set_channel(tmp)
    port_a.set_channel(tmp)
    
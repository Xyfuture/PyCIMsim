from des.base_compo import base_compo
from des.event import event

class uni_channel:
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


class uni_read_port:
    def __init__(self,compo:base_compo,callback):
        self._compo = compo
        self._channel:uni_channel = None
        self._callback = callback

    def read(self,time):
        return self._channel.read_value(time)

    def callback(self):
        next_time = self._compo.next_handle_epsilon
        ent = event(self._compo,self._callback,next_time)
        self._compo.add_event(ent)

    def set_channel(self,channel):
        self._channel = channel


class uni_write_port:
    def __init__(self,compo:base_compo):
        self._compo = compo
        self._channel:uni_channel = None

    def write(self,payload,time):
        f = lambda :self._channel.update_value(payload,time)
        ent = event(self._compo,f,time)
        self._compo.add_event(ent)

    def set_channel(self,channel):
        self._channel = channel



def connect_uni_port(port_a,port_b):
    if isinstance(port_a,uni_read_port) and isinstance(port_b,uni_write_port):
        read_port = port_a
        write_port = port_b
    elif  isinstance(port_b,uni_read_port) and isinstance(port_a,uni_write_port):
        read_port = port_b
        write_port = port_a
    else:
        raise ("wrong port type")

    tmp = uni_channel(read_port,write_port)

    port_a.set_channel(tmp)
    port_a.set_channel(tmp)
    
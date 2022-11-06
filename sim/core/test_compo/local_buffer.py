import queue

from sim.core.compo.base_core_compo import BaseCoreCompo
from sim.core.test_compo.shared_bus import BusPacket
from sim.core.utils.port.bi_port import BiPort
from sim.des.simulator import Simulator
from sim.des.event import Event
from sim.des.base_compo import BaseCompo
from sim.des.stime import Stime

class BufferPacket:
    def __init__(self,payload,type="read"):
        self.payload = payload
        self.type = type


class LocalBuffer(BaseCoreCompo):
    def __init__(self,sim):
        super(LocalBuffer, self).__init__(sim)

        self._matrix_port = BiPort(self, lambda : self.setup_request(1))
        self._vector_port = BiPort(self, lambda : self.setup_request(2))
        self._transfer_port = BiPort(self, lambda : self.setup_request(3))

        self._ports = [0,self._matrix_port,self._vector_port,self._transfer_port]

        self._request_queue = queue.Queue()
        self._busy:bool = False


    def setup_request(self, node_id):
        '''
        1 for matrix
        2 for vector
        3 for transfer
        '''
        self._request_queue.put((node_id,self._ports[node_id].read(self.current_time)))
        self.process_request()

    def process_request(self):
        if not self._busy:
            if not self._request_queue.empty():
                self._busy = True
                node_id,payload = self._request_queue.get()

                latency = 0
                if payload.type == "read":
                    latency = self.get_process_latency()

                elif payload.type == "write":
                    latency = self.get_process_latency()

                f = lambda : self.finish_process(True,node_id)
                self.add_event(Event(self,f,self.current_time+latency))




    def finish_process(self,payload,node_id):
        self._busy = False
        self._ports[node_id].write(payload,self.next_update_epslion)
        self.process_request()

    def get_process_latency(self):
        return 10











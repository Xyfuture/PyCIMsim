import queue
from sim.circuit.module.base_module import BaseModule
from sim.circuit.module.registry import registry
from sim.network.simple.switch import SwitchInterface


class Memory(BaseModule):
    def __init__(self,sim,interface_id,config=None):
        super(Memory, self).__init__(sim)

        self._config = config
        self._interface_id = interface_id

        self.memory_port = SwitchInterface(self,interface_id)

        self._request_buffer_size = 10 # 实际要看config中的配置
        self._request_buffer = queue.Queue(maxsize=self._request_buffer_size)

        self._status = 'idle'

        self.registry_sensitive()

    def initialize(self):
        pass

    def calc_latency(self,payload):
        return 100

    @registry(['memory_port'])
    def buffer_request(self,payload):
        self._request_buffer.put(payload)

        self.handle_request()

        if not self._request_buffer.full():
            self.memory_port.allow_receive()

    def handle_request(self):
        if self._status == 'idle':
            if not self._request_buffer.empty():
                payload = self._request_buffer.get()
                self._status = 'busy'
                self.memory_port.allow_receive() # 可以继续读取了

                latency = self.calc_latency(payload)

                self.make_event(lambda : self.finish_request(payload),self.current_time+latency)

    def finish_request(self,payload):
        access_type = payload['access_type']

        if access_type == 'read':
            src = payload['src']
            read_payload = {'src': 'buffer', 'dst': src, 'data': None, 'data_size': 128}
            self.memory_port.send(read_payload,self.finish_all)
        else:
            self.finish_all()

    def finish_all(self):
        self._status = 'idle'
        self.handle_request()




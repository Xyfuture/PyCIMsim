import queue
from math import ceil

from sim.circuit.module.base_module import BaseModule
from sim.circuit.module.registry import registry
from sim.config.config import MemoryConfig
from sim.core.compo.connection.payloads import MemoryRequest, BusPayload, MemoryReadValue
from sim.network.simple.switch import SwitchInterface


class Memory(BaseModule):
    def __init__(self, sim, interface_id, config: MemoryConfig = None):
        super(Memory, self).__init__(sim)

        self._config = config
        self._interface_id = interface_id

        self.memory_port = SwitchInterface(self, interface_id)

        self._request_buffer_size = 10  # 实际要看config中的配置
        self._request_buffer = queue.Queue(maxsize=self._request_buffer_size)

        self._status = 'idle'

        self.registry_sensitive()

    def initialize(self):
        pass

    def calc_latency(self, memory_request: MemoryRequest):
        data_size = memory_request.data_size
        access_type = memory_request.access_type

        times = ceil(data_size / self._config.data_width)

        if self._config:
            if access_type == 'read':
                self.add_dynamic_energy(self._config.read_energy * times)
                return self._config.read_latency * times
            elif access_type == 'write':
                self.add_dynamic_energy(self._config.write_energy * times)
                return self._config.write_latency * times
        else:
            return 100

    @registry(['memory_port'])
    def buffer_request(self, payload):
        self._request_buffer.put(payload)
        # print(f"memory {len(self._request_buffer.queue)}")

        self.handle_request()

        # if not self._request_buffer.full():
        #     self.memory_port.allow_receive()

    def handle_request(self):
        if self._status == 'idle':  # 如果是busy就不进入
            if not self._request_buffer.empty():
                bus_payload: BusPayload = self._request_buffer.get()
                self._status = 'busy'
                self.memory_port.allow_receive()  # 可以继续读取了

                latency = self.calc_latency(bus_payload.payload)

                self.make_event(lambda: self.finish_request(bus_payload), self.current_time + latency)

    def finish_request(self, bus_payload: BusPayload):
        memory_request = bus_payload.payload
        access_type = memory_request.access_type

        if access_type == 'read':
            read_payload = BusPayload(
                src=self._interface_id, dst=bus_payload.src, data_size=memory_request.data_size,
                payload=MemoryReadValue()
            )
            self.memory_port.send(read_payload, self.finish_all)
        else:
            self.finish_all()

    def finish_all(self):
        self._status = 'idle'
        self.handle_request()

from math import floor, ceil

from sim.circuit.module.registry import registry
from sim.config.config import CoreConfig
from sim.core.compo.base_core_compo import BaseCoreCompo
from sim.core.compo.message_bus import MessageInterface


class LocalBuffer(BaseCoreCompo):
    def __init__(self, sim, config: CoreConfig = None):
        super(LocalBuffer, self).__init__(sim)

        self._core_config = config
        self._config = config.local_buffer

        self.buffer_port = MessageInterface(self, "buffer")

        self.registry_sensitive()

    def initialize(self):
        pass

    def calc_latency(self, payload):
        data_size = payload['data_size']
        access_type = payload['access_type']

        times = ceil(data_size/self._config.data_width)

        if self._config:
            if access_type == 'read':
                self.add_dynamic_energy(self._config.read_energy * times)
                return self._config.read_latency * times
            elif access_type == 'write':
                self.add_dynamic_energy(self._config.write_energy * times)
                return self._config.write_latency * times
        else:
            return 10

    @registry(['buffer_port'])
    def handle_request(self, payload):
        # data_size = payload['data_size']
        # access_type =payload['access_type']

        latency = self.calc_latency(payload)

        self.make_event(lambda: self.finish_request(payload), self.current_time + latency)

    def finish_request(self, payload):
        access_type = payload['access_type']

        if access_type == 'read':
            src = payload['src']
            read_payload = {'src': 'buffer', 'dst': src, 'data': None, 'data_size': 128}
            self.buffer_port.send(read_payload, lambda: self.buffer_port.allow_receive())
        elif access_type == 'write':
            self.buffer_port.allow_receive()

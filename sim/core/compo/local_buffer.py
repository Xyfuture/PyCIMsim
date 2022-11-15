from sim.core.compo.base_core_compo import BaseCoreCompo
from sim.core.compo.message_bus import MessageInterface


class LocalBuffer(BaseCoreCompo):
    def __init__(self, sim, config=None):
        super(LocalBuffer, self).__init__(sim)

        self._config = config

        self.buffer_port = MessageInterface(self, "buffer",self.process)

    def initialize(self):
        pass

    def calc_latency(self,data_size,access_type):
        return 10

    def process(self,payload):
        data_size = payload['data_size']
        access_type =payload['access_type']

        latency = self.calc_latency(data_size,access_type)

        self.make_event(lambda : self.finish_request(payload),self.current_time+latency)


    def finish_request(self,payload):
        access_type =payload['access_type']

        if access_type == 'read':
            src =payload['src']
            read_payload = {'src':'buffer','dst':src,'data':None,'data_size':128}
            self.buffer_port.send(read_payload,lambda : self.buffer_port.allow_receive())
        elif access_type == 'write':
            self.buffer_port.allow_receive()



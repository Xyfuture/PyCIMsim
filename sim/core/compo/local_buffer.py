from sim.core.compo.base_core_compo import BaseCoreCompo
from sim.des.simulator import Simulator
from sim.des.event import Event
from sim.des.base_compo import BaseCompo
from sim.des.stime import Stime
from sim.core.utils.port.uni_port import UniReadPort, UniWritePort
from sim.core.utils.register.register import RegEnable, RegNext
from sim.core.utils.bus.bi_bus import SharedBusPort


class LocalBuffer(BaseCoreCompo):
    def __init__(self, sim, config=None):
        super(LocalBuffer, self).__init__(sim)

        self._config = config

        self.buffer_port = SharedBusPort(self, "buffer", self.handle_request, self.finish_all)

    def initialize(self):
        pass

    def calc_latency(self):
        return 10

    def handle_request(self):
        # payload = self.buffer_port.read()
        # src = payload['src']

        latency = self.calc_latency()
        self.make_event(self.write_reqeust_finish, self.current_time + latency)

    def read_request_finish(self):
        pass

    def write_reqeust_finish(self):
        self.finish_all()

    def finish_all(self):
        self.buffer_port.allow_read_next(True)

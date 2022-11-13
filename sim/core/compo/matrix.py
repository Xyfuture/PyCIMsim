from sim.core.compo.base_core_compo import BaseCoreCompo
from sim.des.simulator import Simulator
from sim.des.event import Event
from sim.des.base_compo import BaseCompo
from sim.des.stime import Stime
from sim.core.utils.port.uni_port import UniReadPort, UniWritePort, make_bind_ports
from sim.core.utils.register.register import RegEnable, RegNext
from sim.core.utils.bus.bi_bus import SharedBusPort


class MatrixUnit(BaseCoreCompo):
    def __init__(self,sim,config=None):
        super(MatrixUnit, self).__init__(sim)
        self._config = config

        self._reg = RegNext(self,None)


        self.id_matrix_port = UniReadPort(self,None)

        self.matrix_buffer = SharedBusPort(self,"matrix",None,None)

        self.matrix_busy = UniWritePort(self)

        self.request_type_read,self.request_type_write = make_bind_ports(self,self.process)



    def initialize(self):
        pass

    def calc_compute_latency(self):
        return 10

    def process(self):
        pass

    def handle_request(self):
        payload = self._reg.read()




    def update_reg(self):
        payload = self.id_matrix_port.read(self.current_time)

        if payload:
            self._reg.write(payload)


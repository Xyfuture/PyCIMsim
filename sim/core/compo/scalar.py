from sim.core.compo.base_core_compo import BaseCoreCompo
from sim.des.simulator import Simulator
from sim.des.event import Event
from sim.des.base_compo import BaseCompo
from sim.des.stime import Stime

from sim.core.utils.port.uni_port import UniReadPort, UniWritePort
from sim.core.utils.register.register import RegEnable, RegNext




class Scalar(BaseCoreCompo):
    def __init__(self,sim):
        super(Scalar, self).__init__(sim)

        self.id_scalar_port = UniReadPort(self,self.update_reg)
        self.reg_file_write = UniWritePort(self)

        self._reg = RegNext(self,self.execute)


    def update_reg(self):
        payload =self.id_scalar_port.read(self.current_time)
        if payload:
            self._reg.write(payload)


    def execute(self):
        payload = self._reg.read()
        op = payload['aluop']
        rd_addr,rs1_data,rs2_data = payload['rd_addr'],payload['rs1_data'],payload['rs2_data']
        rd_data = 0

        if op == 'add':
            rd_data = rs1_data + rs2_data

        self.reg_file_write.write({'rd_addr':rd_addr,'rd_data':rd_data})

    def initialize(self):
        pass


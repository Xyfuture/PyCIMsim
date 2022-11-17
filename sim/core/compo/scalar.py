from sim.circuit.module.registry import registry
from sim.circuit.port.port import UniReadPort, UniWritePort
from sim.circuit.register.register import RegNext
from sim.core.compo.base_core_compo import BaseCoreCompo
from sim.des.simulator import Simulator
from sim.des.event import Event
from sim.des.base_compo import BaseCompo
from sim.des.stime import Stime


class Scalar(BaseCoreCompo):
    def __init__(self,sim):
        super(Scalar, self).__init__(sim)

        self.id_scalar_port = UniReadPort(self)
        self.reg_file_write = UniWritePort(self)

        self._reg = RegNext(self)
        self._reg_read_port = self._reg.get_output_read_port()
        self._reg_write_port = self._reg.get_input_write_port()

        self.registry_sensitive()

    @registry(['id_scalar_port'])
    def update_reg(self):
        payload = self.id_scalar_port.read()
        if payload:
            self._reg_write_port.write(payload)

    @registry(['_reg_read_port'])
    def execute(self):
        payload = self._reg_read_port.read()
        op = payload['aluop']
        rd_addr,rs1_data,rs2_data = payload['rd_addr'],payload['rs1_data'],payload['rs2_data']
        rd_data = 0

        if op == 'add':
            rd_data = rs1_data + rs2_data

        self.reg_file_write.write({'rd_addr':rd_addr,'rd_data':rd_data})

    def initialize(self):
        pass


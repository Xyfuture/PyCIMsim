from sim.circuit.module.registry import registry
# from sim.circuit.port.port import UniReadPort, UniWritePort
from sim.circuit.wire.wire import InWire, UniWire, OutWire, UniPulseWire
from sim.circuit.register.register import RegNext
from sim.core.compo.base_core_compo import BaseCoreCompo
from sim.core.compo.connection.payloads import ScalarInfo
from sim.des.simulator import Simulator
from sim.des.event import Event
from sim.des.base_compo import BaseCompo
from sim.des.stime import Stime


class ScalarUnit(BaseCoreCompo):
    def __init__(self, sim):
        super(ScalarUnit, self).__init__(sim)

        self.id_scalar_port = InWire(UniWire, self)
        self.reg_file_write = OutWire(UniWire, self)

        self._reg = RegNext(self)
        self._reg_input = UniWire(self)
        self._reg_output = UniWire(self)

        self._reg.connect(self._reg_input, self._reg_output)

        self.registry_sensitive()

    @registry(['id_scalar_port'])
    def update_reg(self):
        payload = self.id_scalar_port.read()
        if payload:
            if payload['ex'] == 'scalar':
                self._reg_input.write(payload)

    @registry(['_reg_output'])
    def execute(self):
        scalar_info: ScalarInfo = self._reg_output.read()
        aluop = scalar_info.op
        rd_addr, rs1_data, rs2_data = scalar_info.rd_addr, scalar_info.rs1_data, scalar_info.rs2_data
        rd_data = 0

        if aluop == 'add':
            rd_data = rs1_data + rs2_data
        elif aluop == 'sub':
            rd_data = rs1_data - rs2_data
        elif aluop == 'mul':
            rd_data = rs1_data * rs2_data

        self.reg_file_write.write({'rd_addr': rd_addr, 'rd_data': rd_data})

    def initialize(self):
        pass

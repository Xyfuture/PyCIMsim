from sim.circuit.module.registry import registry
from sim.circuit.wire.wire import InWire, UniWire, OutWire
from sim.circuit.register.register import RegNext
from sim.config.config import CoreConfig
from sim.core.compo.base_core_compo import BaseCoreCompo
from sim.core.compo.connection.payloads import ScalarInfo


class ScalarUnit(BaseCoreCompo):
    def __init__(self, sim, compo, config: CoreConfig):
        super(ScalarUnit, self).__init__(sim, compo)
        self._config = config

        self.id_scalar_port = InWire(UniWire, sim, self)
        self.reg_file_write = OutWire(UniWire, sim, self)

        self._reg = RegNext(sim, self)
        self._reg_input = UniWire(sim, self)
        self._reg_output = UniWire(sim, self)

        self._reg.connect(self._reg_input, self._reg_output)

        self.registry_sensitive()

    @registry(['id_scalar_port'])
    def update_reg(self):
        payload = self.id_scalar_port.read()
        if not payload and (not payload['ex'] == 'scalar'):
            return
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

        self.circuit_add_dynamic_energy(self._config.scalar_energy)

    def initialize(self):
        self.reg_file_write.write(None)

    def get_running_status(self):
        core_id = 0
        if self._parent_compo:
            core_id = self._parent_compo.core_id

        scalar_info = self._reg_output.read()
        info = f"Core:{core_id} ScalarUnit> {scalar_info}"
        return info

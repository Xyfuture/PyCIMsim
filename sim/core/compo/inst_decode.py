from sim.circuit.module.registry import registry
from sim.circuit.wire.wire import InWire, UniWire, OutWire
from sim.circuit.register.register import RegEnable
from sim.config.config import CoreConfig
from sim.core.compo.base_core_compo import BaseCoreCompo
from sim.core.compo.connection.payloads import *


class InstDecode(BaseCoreCompo):
    matrix_inst = {'gemv'}
    vector_inst = {'vmax', 'vadd', 'vsub', 'vmul', 'vmului', 'vact'}
    transfer_inst = {'send', 'recv', 'dram_to_local', 'local_to_dram'}

    def __init__(self, sim, compo, config: CoreConfig):
        super(InstDecode, self).__init__(sim, compo)
        self._config = config

        self._reg = RegEnable(sim, self)

        self.id_enable = InWire(UniWire, sim, self)
        self.if_id_port = InWire(UniWire, sim, self)

        self.id_stall = OutWire(UniWire, sim, self)

        self.id_out = OutWire(UniWire, sim, self)

        # 接收是否忙的信号线
        self.matrix_busy = InWire(UniWire, sim, self)
        self.vector_busy = InWire(UniWire, sim, self)
        self.transfer_busy = InWire(UniWire, sim, self)

        self._reg_output = UniWire(sim, self)
        self._reg.connect(self.if_id_port, self.id_enable, self._reg_output)

        self.registry_sensitive()

    @registry(['_reg_output', 'reg_file_read_data', 'id_enable'])
    def decode_dispatch(self):
        if_payload = self._reg_output.read()

        if not if_payload or not self.id_enable.read():
            # 执行结束
            self.id_out.write(None)
            return

        # 没有信息时为None
        jump_pc_payload = None
        decode_payload = None

        # TODO 重新写一个指令解析器

        inst, pc = if_payload['inst'], if_payload['pc']
        op = inst['op']

        basic_payload = {'pc':pc}

        if op == 'gemv':
            decode_payload = MatrixInfo.load_dict(basic_payload.update(inst))
        elif op in self.vector_inst:
            decode_payload = VectorInfo.load_dict(basic_payload.update(inst))
        elif op in self.transfer_inst:
            decode_payload = TransferInfo.load_dict(basic_payload.update(inst))

        self.id_out.write(decode_payload)

        self.circuit_add_dynamic_energy(self._config.inst_decode_energy)

    @registry(['_reg_output', 'matrix_busy', 'vector_busy', 'transfer_busy'])
    def check_stall(self):
        inst_payload = self._reg_output.read()
        if not inst_payload:
            return

        matrix_busy_payload = self.matrix_busy.read()
        vector_busy_payload = self.vector_busy.read()
        transfer_busy_payload = self.transfer_busy.read()

        stall_info = matrix_busy_payload or vector_busy_payload or transfer_busy_payload

        self.id_stall.write(stall_info)

    def initialize(self):
        self.id_stall.write(False)
        self.id_out.write(None)

        self._reg.init(None)

    def get_running_status(self):
        core_id = 0
        if self._parent_compo:
            core_id = self._parent_compo.core_id

        inst_payload = self._reg_output.read()
        if not inst_payload:
            return f"Core:{core_id} InstDecode> None"
        info = f"Core:{core_id} InstDecode> pc:{inst_payload['pc']} inst:{inst_payload['inst']}"
        return info


class DecodeForward(BaseCoreCompo):
    def __init__(self, sim, compo):
        super(DecodeForward, self).__init__(sim, compo)

        self.id_out = InWire(UniWire, sim, self)

        self.id_matrix_port = OutWire(UniWire, sim, self)
        self.id_vector_port = OutWire(UniWire, sim, self)
        self.id_transfer_port = OutWire(UniWire, sim, self)

        self.registry_sensitive()

        self._map_port = {
            'matrix': self.id_matrix_port,
            'vector': self.id_vector_port,
            'transfer': self.id_transfer_port
        }

    def initialize(self):
        for k, v in self._map_port.items():
            v.write(None)

    @registry(['id_out'])
    def process(self):
        payload = self.id_out.read()

        for k, v in self._map_port.items():
            v.write(None)
        if payload:
            self._map_port[payload['ex']].write(payload)

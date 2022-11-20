from sim.circuit.module.registry import registry
# from sim.circuit.port.port import UniWritePort, UniReadPort
from sim.circuit.wire.wire import InWire, UniWire, OutWire, UniPulseWire
from sim.circuit.register.register import RegEnable
from sim.core.compo.base_core_compo import BaseCoreCompo
from sim.des.simulator import Simulator
from sim.des.event import Event
from sim.des.base_compo import BaseCompo
from sim.des.stime import Stime

from sim.des.utils import fl


class InstDecode(BaseCoreCompo):
    def __init__(self, sim):
        super(InstDecode, self).__init__(sim)

        self._reg = RegEnable(self)

        self.id_enable = InWire(UniWire, self)
        self.if_id_port = InWire(UniWire, self)

        self.id_stall = OutWire(UniWire, self)

        self.jump_pc = OutWire(UniWire, self)

        self.reg_file_read_addr = OutWire(UniWire, self)
        self.reg_file_read_data = InWire(UniWire, self)

        self.id_out = OutWire(UniWire, self)

        # 接收是否忙的信号线
        self.matrix_busy = InWire(UniWire, self)
        # self.vector_busy = UniReadPort(self, self.process)
        # self.transfer_busy = UniReadPort(self, self.process)
        #
        # self.ex_busy = [self.matrix_busy, self.vector_busy, self.transfer_busy]

        # self._stall_reg = RegNext(self,None)

        self._reg_output = UniWire(self)
        self._reg.connect(self.if_id_port, self.id_enable, self._reg_output)

        self.registry_sensitive()

    @registry(['_reg_output'])
    def read_register(self):
        inst_payload = self._reg_output.read()

        reg_read_payload = {'rd_addr': 0, 'rs1_addr': 0, 'rs2_addr': 0}

        if not inst_payload:
            # self.reg_file_read_addr.write(reg_read_payload)
            return

        inst = inst_payload['inst']
        if 'rs1_addr' not in inst and 'rs2_addr' not in inst and 'rd_addr' not in inst:
            return

        for reg in ['rd_addr', 'rs1_addr', 'rs2_addr']:
            if reg in inst:
                reg_read_payload[reg] = inst[reg]

        self.reg_file_read_addr.write(reg_read_payload)

    @registry(['_reg_output', 'reg_file_read_data'])
    def decode_dispatch(self):
        if_payload = self._reg_output.read()
        if not if_payload:
            return
        inst, pc = if_payload['inst'], if_payload['pc']

        reg_payload = self.reg_file_read_data.read()
        rd_data, rs1_data, rs2_data = 0, 0, 0
        if reg_payload:
            rd_data, rs1_data, rs2_data = reg_payload['rd_data'], reg_payload['rs1_data'], reg_payload['rs2_data']

        jump_pc_payload = None
        # decode_payload = {'pc':pc,'inst':inst,'ex':None}
        decode_payload = {'pc':pc,'inst':inst,'ex':None}
        op = inst['op']
        if op == 'seti':
            decode_payload = {'pc': pc, 'inst': inst, 'ex': 'scalar', 'aluop': 'add',
                              'rd_addr': inst['rd_addr'], 'rs1_data': inst['imm'], 'rs2_data': 0}
        elif op == 'sub':
            decode_payload = {'pc': pc, 'inst': inst, 'ex': 'scalar', 'aluop': 'sub',
                              'rd_addr': inst['rd_addr'], 'rs1_data': rs1_data, 'rs2_data': rs2_data}
        elif op == 'add':
            decode_payload = {'pc': pc, 'inst': inst, 'ex': 'scalar', 'aluop': 'add',
                              'rd_addr': inst['rd_addr'], 'rs1_data': rs1_data, 'rs2_data': rs2_data}
        elif op == 'addi':
            decode_payload = {'pc': pc, 'inst': inst, 'ex': 'scalar', 'aluop': 'add',
                              'rd_addr': inst['rd_addr'], 'rs1_data': rs1_data, 'rs2_data': inst['imm']}
        elif op == 'muli':
            decode_payload = {'pc': pc, 'inst': inst, 'ex': 'scalar', 'aluop': 'mul',
                              'rd_addr': inst['rd_addr'], 'rs1_data': rs1_data, 'rs2_data': inst['imm']}
        elif op == 'mul':
            decode_payload = {'pc': pc, 'inst': inst, 'ex': 'scalar', 'aluop': 'mul',
                              'rd_addr': inst['rd_addr'], 'rs1_data': rs1_data, 'rs2_data': rs2_data}

        elif op == 'j':
            jump_pc_payload = {'offset': inst['offset']}
        elif op == 'jnei':
            if rd_data != inst['imm']:
                jump_pc_payload = {'offset': inst['offset']}
        elif op == 'jne':
            if rs1_data != rs2_data:
                jump_pc_payload = {'offset': inst['offset']}

        elif op == 'gemv':
            decode_payload = {'pc': pc, 'inst': inst, 'ex': 'matrix', 'aluop': 'gemv',
                              }

        elif op == 'vmax':
            decode_payload = {'ex':'vector','aluop':'vmax',
                              'out_addr':rd_data,'in1_addr':rs1_data,'in2_addr':rs2_data,'len':inst['len']}
        elif op == 'vadd':
            decode_payload = {'ex': 'vector', 'aluop': 'vadd',
                              'out_addr': rd_data, 'in1_addr': rs1_data, 'in2_addr': rs2_data, 'len': inst['len']}
        elif op == 'vsub':
            decode_payload = {'ex': 'vector', 'aluop': 'vsub',
                              'out_addr': rd_data, 'in1_addr': rs1_data, 'in2_addr': rs2_data, 'len': inst['len']}
        elif op == 'vmul':
            decode_payload = {'ex': 'vector', 'aluop': 'vmul',
                              'out_addr': rd_data, 'in1_addr': rs1_data, 'in2_addr': rs2_data, 'len': inst['len']}
        elif op == 'vmului':
            decode_payload = {'ex': 'vector', 'aluop': 'vmului',
                              'out_addr': rd_data, 'in1_addr': rs1_data, 'imm': inst['imm'], 'len': inst['len']}
        elif op == 'vact':
            decode_payload = {'ex': 'vector', 'aluop': 'vact',
                              'out_addr': rd_data, 'in1_addr': rs1_data, 'type': inst['type'], 'len': inst['len']}

        elif op == 'sync':
            pass
        elif op == 'wait_core':
            pass
        elif op == 'inc_state':
            pass

        self.id_out.write(decode_payload)
        self.jump_pc.write(jump_pc_payload)

    @registry(['_reg_output', 'matrix_busy'])
    def check_stall(self):
        inst_payload = self._reg_output.read()
        if not inst_payload:
            return

        matrix_busy_payload = self.matrix_busy.read()
        if not matrix_busy_payload:
            return

        inst = inst_payload['inst']
        busy = matrix_busy_payload['busy']
        self.id_stall.write(False)
        if inst['op'] == 'gemv':
            if busy:
                self.id_stall.write(True)

    def initialize(self):
        self.id_stall.write(False)


class DecodeForward(BaseCoreCompo):
    def __init__(self, sim):
        super(DecodeForward, self).__init__(sim)

        self.id_out = InWire(UniWire, self)

        self.id_matrix_port = OutWire(UniWire, self)
        self.id_vector_port = OutWire(UniWire, self)
        self.id_transfer_port = OutWire(UniWire, self)
        self.id_scalar_port = OutWire(UniWire, self)

        self.registry_sensitive()

    def initialize(self):
        pass

    @registry(['id_out'])
    def process(self):
        payload = self.id_out.read()

        self.id_matrix_port.write(payload)
        self.id_vector_port.write(payload)
        self.id_transfer_port.write(payload)
        self.id_scalar_port.write(payload)

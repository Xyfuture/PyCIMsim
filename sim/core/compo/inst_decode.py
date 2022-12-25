from sim.circuit.module.registry import registry
# from sim.circuit.port.port import UniWritePort, UniReadPort
from sim.circuit.wire.wire import InWire, UniWire, OutWire, UniPulseWire
from sim.circuit.register.register import RegEnable
from sim.core.compo.base_core_compo import BaseCoreCompo
from sim.core.compo.connection.payloads import *
from sim.des.simulator import Simulator
from sim.des.event import Event
from sim.des.base_compo import BaseCompo
from sim.des.stime import Stime

from sim.des.utils import fl


class InstDecode(BaseCoreCompo):
    matrix_inst = {'gemv'}
    vector_inst = {'vmax', 'vadd', 'vsub', 'vmul', 'vmului', 'vact'}
    transfer_inst = {'sync', 'wait_core', 'inc_state',
                     'dram_to_global', 'global_to_dram', 'global_to_local',
                     'global_clr', 'global_cpy', 'local_clr', 'local_cpy'}

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
        self.vector_busy = InWire(UniWire, self)
        self.transfer_busy = InWire(UniWire, self)
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

    @registry(['_reg_output', 'reg_file_read_data', 'id_enable'])
    def decode_dispatch(self):
        if_payload = self._reg_output.read()
        if not if_payload:
            return
        inst, pc = if_payload['inst'], if_payload['pc']

        reg_payload = self.reg_file_read_data.read()
        rd_data, rs1_data, rs2_data = 0, 0, 0
        if reg_payload:
            rd_data, rs1_data, rs2_data = reg_payload['rd_data'], reg_payload['rs1_data'], reg_payload['rs2_data']

        # 没有信息时为None
        jump_pc_payload = None
        decode_payload = None

        if not self.id_enable.read():
            self.id_out.write(decode_payload)
            self.jump_pc.write(jump_pc_payload)
            return

        op = inst['op']
        if op == 'seti':
            decode_payload = ScalarInfo.load_dict({'pc': pc, 'ex': 'scalar', 'op': 'add',
                                                   'rd_addr': inst['rd_addr'], 'rs1_data': inst['imm'],
                                                   'rs2_data': 0})
        elif op == 'sub':
            decode_payload = ScalarInfo.load_dict({'pc': pc, 'ex': 'scalar', 'op': 'sub',
                                                   'rd_addr': inst['rd_addr'], 'rs1_data': rs1_data,
                                                   'rs2_data': rs2_data})
        elif op == 'add':
            decode_payload = ScalarInfo.load_dict({'pc': pc, 'ex': 'scalar', 'op': 'add',
                                                   'rd_addr': inst['rd_addr'], 'rs1_data': rs1_data,
                                                   'rs2_data': rs2_data})
        elif op == 'addi':
            decode_payload = ScalarInfo.load_dict({'pc': pc, 'ex': 'scalar', 'op': 'add',
                                                   'rd_addr': inst['rd_addr'], 'rs1_data': rs1_data,
                                                   'rs2_data': inst['imm']})
        elif op == 'muli':
            decode_payload = ScalarInfo.load_dict({'pc': pc, 'ex': 'scalar', 'op': 'mul',
                                                   'rd_addr': inst['rd_addr'], 'rs1_data': rs1_data,
                                                   'rs2_data': inst['imm']})
        elif op == 'mul':
            decode_payload = ScalarInfo.load_dict({'pc': pc, 'ex': 'scalar', 'op': 'mul',
                                                   'rd_addr': inst['rd_addr'], 'rs1_data': rs1_data,
                                                   'rs2_data': rs2_data})

        # 这种情况下 decode_payload是空的
        elif op == 'j':
            jump_pc_payload = {'offset': inst['offset']}
        elif op == 'jnei':
            if rd_data != inst['imm']:
                jump_pc_payload = {'offset': inst['offset']}
        elif op == 'jne':
            if rs1_data != rs2_data:
                jump_pc_payload = {'offset': inst['offset']}

        elif op == 'gemv':
            decode_payload = MatrixInfo.load_dict({'pc': pc, 'inst': inst, 'ex': 'matrix', 'op': 'gemv',
                                                   'out_addr': rd_data, 'vec_addr': rs1_data,
                                                   'pe_assign': inst['pe_assign'],
                                                   'relu': inst['relu']})

        elif op == 'vmax':
            decode_payload = VectorInfo.load_dict({'pc': pc, 'ex': 'vector', 'op': 'vmax',
                                                   'out_addr': rd_data, 'in1_addr': rs1_data, 'in2_addr': rs2_data,
                                                   'vec_len': inst['len']})
        elif op == 'vadd':
            decode_payload = VectorInfo.load_dict({'pc': pc, 'ex': 'vector', 'op': 'vadd',
                                                   'out_addr': rd_data, 'in1_addr': rs1_data, 'in2_addr': rs2_data,
                                                   'vec_len': inst['len']})
        elif op == 'vsub':
            decode_payload = VectorInfo.load_dict({'pc': pc, 'ex': 'vector', 'op': 'vsub',
                                                   'out_addr': rd_data, 'in1_addr': rs1_data, 'in2_addr': rs2_data,
                                                   'vec_len': inst['len']})
        elif op == 'vmul':
            decode_payload = VectorInfo.load_dict({'pc': pc, 'ex': 'vector', 'op': 'vmul',
                                                   'out_addr': rd_data, 'in1_addr': rs1_data, 'in2_addr': rs2_data,
                                                   'vec_len': inst['len']})
        elif op == 'vmului':
            decode_payload = VectorInfo.load_dict({'pc': pc, 'ex': 'vector', 'op': 'vmului',
                                                   'out_addr': rd_data, 'in1_addr': rs1_data, 'imm': inst['imm'],
                                                   'vec_len': inst['len']})
        elif op == 'vact':
            decode_payload = VectorInfo.load_dict({'pc': pc, 'ex': 'vector', 'op': 'vact',
                                                   'out_addr': rd_data, 'in1_addr': rs1_data, 'act_type': inst['type'],
                                                   'vec_len': inst['len']})

        elif op == 'sync':
            decode_payload = TransferInfo.load_dict({
                'pc': pc, 'ex': 'transfer', 'op': 'sync',
                'sync_info': SyncInfo.load_dict({'start_core': inst['start_core'], 'end_core': inst['end_core']})
            })
        elif op == 'wait_core':
            decode_payload = TransferInfo.load_dict({
                'pc': pc, 'ex': 'transfer', 'op': 'wait_core',
                'sync_info': SyncInfo.load_dict({'state': inst['state'], 'core_id': inst['core_id']})
            })
        elif op == 'inc_state':
            decode_payload = TransferInfo.load_dict({
                'pc': pc, 'ex': 'transfer', 'op': 'inc_state',
                'sync_info': SyncInfo()
            })

        elif op == 'dram_to_global':
            decode_payload = TransferInfo.load_dict({
                'pc': pc, 'ex': 'transfer', 'op':'dram_to_global',
                'mem_access_info':MemAccessInfo.load_dict({
                    'dst_addr':inst['dst_addr'],'src_addr':inst['src_addr'],'data_size':inst['data_size']})
            })
        elif op == 'global_to_dram':
            decode_payload = TransferInfo.load_dict({
                'pc': pc, 'ex': 'transfer', 'op': 'global_to_dram',
                'mem_access_info': MemAccessInfo.load_dict({
                    'dst_addr': inst['dst_addr'], 'src_addr': inst['src_addr'], 'data_size': inst['data_size']})
            })
        elif op == 'global_to_local':
            decode_payload = TransferInfo.load_dict({
                'pc': pc, 'ex': 'transfer', 'op': 'global_to_local',
                'mem_access_info': MemAccessInfo.load_dict({
                    'dst_addr': inst['dst_addr'], 'src_addr': inst['src_addr'], 'data_size': inst['data_size']})
            })
        elif op == 'local_to_global':
            decode_payload = TransferInfo.load_dict({
                'pc': pc, 'ex': 'transfer', 'op': 'local_to_global',
                'mem_access_info': MemAccessInfo.load_dict({
                    'dst_addr': inst['dst_addr'], 'src_addr': inst['src_addr'], 'data_size': inst['data_size']})
            })
        elif op == 'global_clr':
            decode_payload = TransferInfo.load_dict({
                'pc': pc, 'ex': 'transfer', 'op':'global_clr',
                'mem_access_info':MemAccessInfo.load_dict({
                    'dst_addr':inst['dst_addr'], 'data_size':inst['data_size']})
            })
        elif op == 'local_clr':
            decode_payload = TransferInfo.load_dict({
                'pc': pc, 'ex': 'transfer', 'op': 'local_clr',
                'mem_access_info': MemAccessInfo.load_dict({
                    'dst_addr': inst['dst_addr'], 'data_size': inst['data_size']})
            })
        elif op == 'global_cpy':
            decode_payload = TransferInfo.load_dict({
                'pc': pc, 'ex': 'transfer', 'op': 'dram_to_global',
                'mem_access_info': MemAccessInfo.load_dict({
                    'dst_addr': inst['dst_addr'], 'src_addr': inst['src_addr'], 'data_size': inst['data_size']})
            })
        elif op == 'local_cpy':
            decode_payload = TransferInfo.load_dict({
                'pc': pc, 'ex': 'transfer', 'op': 'dram_to_global',
                'mem_access_info': MemAccessInfo.load_dict({
                    'dst_addr': inst['dst_addr'], 'src_addr': inst['src_addr'], 'data_size': inst['data_size']})
            })

        self.id_out.write(decode_payload)
        self.jump_pc.write(jump_pc_payload)

    @registry(['_reg_output', 'matrix_busy', 'vector_busy', 'transfer_busy'])
    def check_stall(self):
        inst_payload = self._reg_output.read()
        if not inst_payload:
            return

        matrix_busy_payload = self.matrix_busy.read()
        vector_busy_payload = self.vector_busy.read()
        transfer_busy_payload = self.transfer_busy.read()

        inst = inst_payload['inst']
        op = inst['op']

        # stall_info = False
        # if op in self.matrix_inst and matrix_busy_payload:
        #     stall_info = True
        # elif op in self.vector_inst and vector_busy_payload:
        #     stall_info = True
        # elif op in self.transfer_inst and transfer_busy_payload:
        #     stall_info = True
        stall_info = matrix_busy_payload or vector_busy_payload or transfer_busy_payload

        self.id_stall.write(stall_info)

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

        self._map_port = {
            'matrix': self.id_matrix_port,
            'vector': self.id_vector_port,
            'transfer': self.id_transfer_port,
            'scalar': self.id_scalar_port
        }

    def initialize(self):
        pass

    @registry(['id_out'])
    def process(self):
        payload = self.id_out.read()

        # if not payload:
        #     for k,v in self._map_port.items():
        #         v.write(payload)
        #
        # for port_name in self._map_port:
        #     if port_name == payload['ex']:
        #         self._map_port[port_name].write(payload)
        #     else:
        #         self._map_port[port_name].write(None)

        for k, v in self._map_port:
            v.write(None)
        if payload:
            self._map_port[payload['ex']].write(payload)

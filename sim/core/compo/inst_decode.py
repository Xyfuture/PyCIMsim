from sim.circuit.module.registry import registry
from sim.circuit.port.port import UniWritePort, UniReadPort
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
        # self.id_enable, self.if_id_port = self._reg.get_wires()
        self._reg_read_port = self._reg.get_output_read_port()
        self.if_id_port = self._reg.get_input_read_port()
        self.id_enable = self._reg.get_enable_read_port()

        self.id_stall = UniWritePort(self)

        self.jump_pc = UniWritePort(self)

        self.reg_file_read_addr = UniWritePort(self)
        self.reg_file_read_data = UniReadPort(self)

        # 发送到不同的 端口 实际上一条线,但是方便了模拟
        self.id_matrix_port = UniWritePort(self)
        self.id_vector_port = UniWritePort(self)
        self.id_transfer_port = UniWritePort(self)
        self.id_scalar_port = UniWritePort(self)
        self.id_ex_ports = [self.id_matrix_port, self.id_vector_port,
                            self.id_transfer_port, self.id_scalar_port]

        # 接收是否忙的信号线
        self.matrix_busy = UniReadPort(self)
        # self.vector_busy = UniReadPort(self, self.process)
        # self.transfer_busy = UniReadPort(self, self.process)
        #
        # self.ex_busy = [self.matrix_busy, self.vector_busy, self.transfer_busy]

        # self._stall_reg = RegNext(self,None)

        self.registry_sensitive()

    @registry(['_reg_read_port'])
    def read_register(self):
        inst_payload = self._reg_read_port.read()

        reg_read_payload = {'rs1_addr': 0, 'rs2_addr': 0}

        if not inst_payload:
            # self.reg_file_read_addr.write(reg_read_payload)
            return

        inst = inst_payload['inst']
        if 'rs1_addr' not in inst and 'rs2_addr' not in inst:
            # self.reg_file_read_addr.write(reg_read_payload)
            return

        for reg in ['rs1_addr', 'rs2_addr']:
            if reg in inst:
                reg_read_payload[reg] = inst[reg]

        self.reg_file_read_addr.write(reg_read_payload)

    @registry(['_reg_read_port','reg_file_read_data'])
    def decode_dispatch(self):

        inst_payload = self._reg_read_port.read()

        if not inst_payload:
            return

        inst, pc = inst_payload['inst'], inst_payload['pc']

        reg_payload = self.reg_file_read_data.read()

        rs1_data, rs2_data = 0, 0
        if reg_payload:
            rs1_data, rs2_data = reg_payload['rs1_data'], reg_payload['rs2_data']

        op = inst['op']

        self.jump_pc.write(None)
        if op == 'add':
            rd_addr = inst['rd_addr']
            decode_payload = {'pc': pc, 'inst': inst, 'aluop': 'add', 'rd_addr': rd_addr, 'rs1_data': rs1_data,
                              'rs2_data': rs2_data}
            self.id_scalar_port.write(decode_payload)
        elif op == 'addi':
            rd_addr = inst['rd_addr']
            imm = inst['imm']
            decode_payload = {'pc': pc, 'inst': inst, 'aluop': 'add', 'rd_addr': rd_addr, 'rs1_data': rs1_data,
                              'rs2_data': imm}
            self.id_scalar_port.write(decode_payload)
        elif op == 'j':
            imm = inst['imm']
            self.jump_pc.write({'offset': imm})
        elif op == 'gemv':
            decode_payload = {'pc': pc, 'inst': inst, 'op': op}
            self.id_matrix_port.write(decode_payload)

    @registry(['_reg_read_port','matrix_busy'])
    def check_stall(self):
        inst_payload = self._reg_read_port.read()
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

        # for port in self.id_ex_ports:
        #     port.write(None, self.current_time)

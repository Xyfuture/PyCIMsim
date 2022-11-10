from sim.core.compo.base_core_compo import BaseCoreCompo
from sim.des.simulator import Simulator
from sim.des.event import Event
from sim.des.base_compo import BaseCompo
from sim.des.stime import Stime

from sim.core.utils.port.uni_port import UniReadPort, UniWritePort
from sim.core.utils.register.register import RegEnable


class InstFetch(BaseCoreCompo):
    def __init__(self, sim):
        super(InstFetch, self).__init__(sim)

        self._reg = RegEnable(self, self.process)
        self.id_enable, self.if_id_port = self._reg.init_ports()
        self.id_stall = UniWritePort(self)

        self.jump_pc = UniWritePort(self)

        self.reg_file_read_addr = UniWritePort(self)
        self.reg_file_read_data = UniReadPort(self, self.finish_read_reg_file)

        self._reg_file_callback = None

        # 发送到不同的 端口 实际上一条线,但是方便了模拟
        self.id_matrix_port = UniWritePort(self)
        self.id_vector_port = UniWritePort(self)
        self.id_transfer_port = UniWritePort(self)
        self.id_scalar_port = UniWritePort(self)
        self.id_ex_ports = [self.id_matrix_port, self.id_vector_port,
                            self.id_transfer_port, self.id_scalar_port]

        # 接收是否忙的信号线
        self.matrix_busy = UniReadPort(self, self.process)
        self.vector_busy = UniReadPort(self, self.process)
        self.transfer_busy = UniReadPort(self, self.process)

        self.ex_busy = [self.matrix_busy, self.vector_busy, self.transfer_busy]

    def initialize(self):
        self.id_stall.write(False, self.next_update_epsilon)

        for port in self.id_ex_ports:
            port.write(None, self.current_time)

    def process(self):
        payload = self._reg.read()
        pc, inst = payload['pc'], payload['inst']

        self._reg_file_callback = None

        if inst.op == 'jmp':
            offset = inst.imm
            self.jump_pc.write({'valid': True, 'pc': pc + offset}, self.next_update_epsilon)
        elif inst.op == 'add':
            rs1 = inst.rs1
            rs2 = inst.rs2
            # rd = inst.rd
            self.reg_file_read_addr.write({'rs1': rs1, 'rs2': rs2}, self.current_time)

        elif inst.op == 'seti':
            imm = inst.imm
            rd = inst.rd
            decode = {'pc': pc, 'op': 'seti', 'rd': rd, 'rs1_data': imm}

            self.id_scalar_port.write(decode, self.current_time)

    def decode(self ):
        pass

    def add_callback(self):
        payload = self.reg_file_read_data.read(self.current_time)
        rs1_data, rs2_data = payload['rs1_data'], payload['rs2_data']
        payload = self._reg.read(self.current_time)
        pc, inst = payload['pc'], payload['inst']
        decode = {'pc': pc, 'op': 'add', 'rd': inst.rd, 'rs1_data': rs1_data, 'rs2_data': rs2_data}

        self.id_scalar_port.write(decode, self.current_time)

    def finish_read_reg_file(self):
        if callable(self._reg_file_callback):
            self._reg_file_callback()

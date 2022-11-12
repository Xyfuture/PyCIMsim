from sim.core.compo.base_core_compo import BaseCoreCompo
from sim.des.simulator import Simulator
from sim.des.event import Event
from sim.des.base_compo import BaseCompo
from sim.des.stime import Stime

from sim.core.utils.port.uni_port import UniReadPort, UniWritePort
from sim.core.utils.register.register import RegEnable, RegNext
from sim.des.utils import fl


class InstDecode(BaseCoreCompo):
    def __init__(self, sim):
        super(InstDecode, self).__init__(sim)

        self._reg = RegEnable(self, fl(self.read_register,self.decode_dispatch))
        self.id_enable, self.if_id_port = self._reg.init_ports()
        self.id_stall = UniWritePort(self)

        self.jump_pc = UniWritePort(self)

        self.reg_file_read_addr = UniWritePort(self)
        self.reg_file_read_data = UniReadPort(self, self.decode_dispatch)

        # 发送到不同的 端口 实际上一条线,但是方便了模拟
        self.id_matrix_port = UniWritePort(self)
        self.id_vector_port = UniWritePort(self)
        self.id_transfer_port = UniWritePort(self)
        self.id_scalar_port = UniWritePort(self)
        self.id_ex_ports = [self.id_matrix_port, self.id_vector_port,
                            self.id_transfer_port, self.id_scalar_port]

        # 接收是否忙的信号线
        # self.matrix_busy = UniReadPort(self, self.process)
        # self.vector_busy = UniReadPort(self, self.process)
        # self.transfer_busy = UniReadPort(self, self.process)
        #
        # self.ex_busy = [self.matrix_busy, self.vector_busy, self.transfer_busy]

        self._stall_reg = RegNext(self,None)

    def read_register(self):
        inst_payload = self._reg.read()
        if not inst_payload:
            return

        inst = inst_payload['inst']

        if 'rs1_addr' not in inst and 'rs2_addr' not in inst:
            return
        reg_read_payload = {'rs1_addr':0,'rs2_addr':0}
        for reg in ['rs1_addr','rs2_addr']:
            if reg in inst:
                reg_read_payload[reg] = inst[reg]

        self.reg_file_read_addr.write(reg_read_payload,self.next_update_epsilon)

    def decode_dispatch(self):
        # def ex_busy_status():
        #     busy_status = {}
        #     for i,ex_name in enumerate(['matrix','vector','transfer']):
        #         busy_status[ex_name] = self.ex_busy[i].read()['busy']
        #     return busy_status

        inst_payload = self._reg.read()

        if not inst_payload:
            return

        inst,pc = inst_payload['inst'],inst_payload['pc']

        reg_payload = self.reg_file_read_data.read(self.current_time)
        rs1_data,rs2_data = 0,0
        if reg_payload:
            rs1_data, rs2_data = reg_payload['rs1_data'],reg_payload['rs2_data']

        # busy_payload = ex_busy_status()

        op = inst['op']
        if op == 'add':
            rd_addr = inst['rd_addr']
            decode_payload = {'pc':pc,'inst':inst,'aluop':'add','rd_addr':rd_addr,'rs1_data':rs1_data,'rs2_data':rs2_data}
            self.id_scalar_port.write(decode_payload)
        elif op == 'addi':
            rd_addr = inst['rd_addr']
            imm = inst['imm']
            decode_payload = {'pc': pc, 'inst': inst,'aluop':'add','rd_addr': rd_addr, 'rs1_data': rs1_data, 'rs2_data': imm}
            self.id_scalar_port.write(decode_payload)
        elif op == 'j':
            imm = inst['imm']
            self.jump_pc.write({'offset':imm})


    def initialize(self):
        self.id_stall.write(False)

        # for port in self.id_ex_ports:
        #     port.write(None, self.current_time)

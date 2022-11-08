from sim.core.compo.base_core_compo import BaseCoreCompo
from sim.des.simulator import Simulator
from sim.des.event import Event
from sim.des.base_compo import BaseCompo
from sim.des.stime import Stime

from sim.core.utils.port.uni_port import UniReadPort,UniWritePort
from sim.core.utils.register.register import RegEnable



class InstFetch(BaseCoreCompo):
    def __init__(self,sim):
        super(InstFetch, self).__init__(sim)

        # self._pc = 0
        self._inst_buffer = []

        self._pc = RegEnable(self,self.process)

        self.if_id_port = UniWritePort(self)

        self.jump_pc = UniReadPort(self,self.process)

        self.if_enable,self._pc_in = self._pc.init_ports()
        self.if_stall = UniWritePort(self)


    # def process_jump(self):
    #     jump_payload = self.jump_pc.read(self.current_time)
    #     if jump_payload['valid']:
    #         self.if_id_port.write({'pc': -1, 'inst': None}, self.current_time)
    #         self._pc_in.write(jump_payload['pc'])

    # def simple_process(self):
    #     pc = self._pc.read(self.current_time)
    #     inst = self._inst_buffer[pc]
    #     self.if_id_port.write({'pc': pc, 'inst': inst}, self.current_time)
    #     self._pc_in.write(pc + 1)


    def process(self):
        self.fetch_inst()
        self.update_pc()


    def fetch_inst(self):
        jump_payload = self.jump_pc.read()

        if jump_payload:
            self.if_id_port.write({'pc':-1,'inst':None},self.next_update_epslion)
        else:
            pc = self._pc.read()
            inst = self._inst_buffer[pc]
            self.if_id_port.write({'pc':pc,'inst':inst},self.next_update_epslion)

    def update_pc(self):
        jump_payload = self.jump_pc.read()
        # 如果这个周期内没发送jump,那么就不更新
        if jump_payload :
            self._pc_in.write(jump_payload['pc'],self.next_update_epslion)
        else:
            old_pc = self._pc.read()
            self._pc_in.write(old_pc + 1,self.next_update_epslion)


    def initialize(self):
        self._pc.initialize(0)

        self.if_stall.write(False,self.next_update_epslion)
        self._pc_in.write(0,self.next_update_epslion)

        self.if_id_port.write(None,self.next_update_epslion)


    def set_inst_buffer(self,inst_buffer):
        self._inst_buffer = inst_buffer

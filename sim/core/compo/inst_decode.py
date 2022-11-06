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

        self._reg = RegEnable(self,self.process)
        self.id_enable,self.if_id_port = self._reg.init_ports()
        self.id_stall = UniWritePort(self)

        self.jump_pc = UniWritePort(self)

        self.id_ex_port = UniWritePort(self)

        self.reg_file_read_addr = UniWritePort(self)
        self.reg_file_read_data = UniReadPort(self,self.finish_read_reg_file)

    def initialize(self):
        self.id_stall.write(False,self.current_time)
        self.id_ex_port.write(None,self.current_time)

    def process(self):
        payload = self._reg.read(self.current_time)
        pc,inst = payload['pc'],payload['inst']

        # jump
        if inst.op == 'jmp':
            offset = inst.imm


    def finish_read_reg_file(self):
        pass



class BroadcastID(BaseCoreCompo):
    def __init__(self,sim):
        super(BroadcastID, self).__init__(sim)

    def initialize(self):
        pass

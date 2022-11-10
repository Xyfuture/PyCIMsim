from sim.core.compo.base_core_compo import BaseCoreCompo
from sim.des.simulator import Simulator
from sim.des.event import Event
from sim.des.base_compo import BaseCompo
from sim.des.stime import Stime

from sim.core.utils.port.uni_port import UniReadPort,UniWritePort
from sim.core.utils.register.register import RegEnable



class InstFetch(BaseCoreCompo):
    def __init__(self, sim):
        super().__init__(sim)

        self.if_stall = UniWritePort(self)
        self.if_id_port = UniWritePort(self)

        self.reg = RegEnable(self,self.update_pc)

        self.if_enable, _ = self.reg.init_ports()


        self._pc = 0

        self._data = [  "hello",
                        "world",
                        "I'm",
                        "robot",
                        "error"  ]


    def initialize(self):
        self.if_stall.write(False, self.next_update_epsilon)
        self.if_id_port.write(None, self.next_update_epsilon)

    def update_pc(self):
        if self._pc < 4:
            self.if_id_port.write(self._data[self._pc], self.next_update_epsilon)

            self._pc += 1
        else:
            self.if_stall.write(True, self.current_time)



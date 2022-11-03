from sim.core.compo.base_core_compo import BaseCoreCompo
from sim.des.simulator import Simulator
from sim.des.event import Event
from sim.des.base_compo import BaseCompo
from sim.des.stime import Stime

from sim.core.utils.port.uni_port import UniReadPort,UniWritePort
from sim.core.utils.register.register import RegEnable


class Controller(BaseCoreCompo):
    def __init__(self,sim):
        super().__init__(sim)

        self.if_stall = UniReadPort(self, self.process)
        self.id_stall = UniReadPort(self, self.process)

        self.if_enable = UniWritePort(self)
        self.id_enable = UniWritePort(self)

    def initialize(self):
        pass


    def process(self):
        print(not self.if_stall.read(self.current_time))
        self.if_enable.write(not self.if_stall.read(self.current_time), self.current_time)
        self.id_enable.write(not self.id_stall.read(self.current_time), self.current_time)
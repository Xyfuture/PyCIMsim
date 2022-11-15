from sim.circuit.module.registry import registry
from sim.circuit.port.port import UniReadPort, UniWritePort
from sim.core.compo.base_core_compo import BaseCoreCompo
from sim.des.simulator import Simulator
from sim.des.event import Event
from sim.des.base_compo import BaseCompo
from sim.des.stime import Stime




class Controller(BaseCoreCompo):
    def __init__(self,sim):
        super().__init__(sim)

        self.if_stall = UniReadPort(self)
        self.id_stall = UniReadPort(self)

        self.if_enable = UniWritePort(self)
        self.id_enable = UniWritePort(self)

        self.registry_sensitive()

    def initialize(self):
        pass

    @registry(['if_stall','id_stall'])
    def process(self):

        if_status = self.if_stall.read()
        id_status = self.id_stall.read()

        if id_status:
            self.if_enable.write(False)
            self.id_enable.write(False)
        elif if_status:
            self.if_enable.write(False)
            self.id_enable.write(True)
        else :
            self.if_enable.write(True)
            self.id_enable.write(True)

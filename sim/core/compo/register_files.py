from sim.core.compo.base_core_compo import BaseCoreCompo
from sim.des.simulator import Simulator
from sim.des.event import Event
from sim.des.base_compo import BaseCompo
from sim.des.stime import Stime
from sim.core.utils.port.uni_port import UniReadPort, UniWritePort
from sim.core.utils.register.register import RegEnable,RegNext


class RegisterFiles(BaseCoreCompo):
    def __init__(self, sim):
        super(RegisterFiles, self).__init__(sim)

        self.reg_file_read_addr = UniReadPort(self, self.process)
        self.reg_file_read_data = UniWritePort(self)

        self.reg_file_write_addr = UniReadPort(self, self.process)
        self.reg_file_write_data = UniReadPort(self, self.process)

        self._reg_files = RegNext(self,None)

    def initialize(self):
        pass

    def process(self):
        pass

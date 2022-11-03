from sim.core.compo.base_core_compo import BaseCoreCompo
from sim.des.simulator import Simulator
from sim.des.event import Event
from sim.des.base_compo import BaseCompo
from sim.des.stime import Stime

from sim.core.utils.port.uni_port import UniReadPort, UniWritePort
from sim.core.utils.register.register import RegEnable


class InstDecode(BaseCoreCompo):
    def __init__(self, sim):
        super().__init__(sim)

        self.id_stall = UniWritePort(self)

        self.reg = RegEnable(self, self.process)

        self.id_enable, self.if_id_port = self.reg.init_ports()

        self._cnt = 0


    def initialize(self):
        self.id_stall.write(False, self.next_update_epslion)

    def process(self):
        data = self.reg.read(self.current_time)

        print("Inst Decode time:{} , content:{}".format(self.current_time, data))
        self._cnt += 1
        if self._cnt > 4:
            self.id_stall.write(True, self.current_time)
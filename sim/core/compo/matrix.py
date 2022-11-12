from sim.core.compo.base_core_compo import BaseCoreCompo
from sim.des.simulator import Simulator
from sim.des.event import Event
from sim.des.base_compo import BaseCompo
from sim.des.stime import Stime
from sim.core.utils.port.uni_port import UniReadPort, UniWritePort
from sim.core.utils.register.register import RegEnable, RegNext



class MatrixUnit(BaseCoreCompo):
    def __init__(self,sim,config=None):
        super(MatrixUnit, self).__init__(sim)
        self._config = config

        self._reg = RegNext(self,None)

        self.id_matrix_port = UniReadPort(self,None)

        self.matrix_busy = UniWritePort(self)

        # self.



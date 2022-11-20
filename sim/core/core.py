from sim.core.compo.local_buffer import LocalBuffer
from sim.core.compo.matrix import MatrixUnit
from sim.core.compo.message_bus import MessageBus
from sim.core.compo.transfer import TransferUnit
from sim.core.compo.vector import VectorUnit
from sim.des.base_compo import BaseCompo
from sim.core.compo.inst_fetch import InstFetch
from sim.core.compo.inst_decode import InstDecode, DecodeForward
from sim.core.compo.register_files import RegisterFiles
from sim.core.compo.scalar import ScalarUnit
from sim.core.compo.controller import Controller


class Core(BaseCompo):
    def __init__(self,sim,inst_buffer,core_id,noc,config=None):
        super(Core, self).__init__(sim)

        self._config = config
        self._inst_buffer = inst_buffer
        self.core_id = core_id

        self.inst_fetch = InstFetch(sim)
        self.inst_decode = InstDecode(sim)
        self.forward = DecodeForward(sim)
        self.ctrl = Controller(sim)
        self.reg_file = RegisterFiles(sim)

        self.scalar = ScalarUnit(sim)
        self.vector = VectorUnit(sim,self._config)
        self.matrix = MatrixUnit(sim,self._config)
        self.transfer = TransferUnit(sim,self.core_id,self._config)

        self.bus = MessageBus(sim,self._config)
        self.buffer = LocalBuffer(sim,self._config)

        self.inst_fetch // self.inst_decode
        self.inst_fetch // self.ctrl

        self.inst_decode // self.forward
        self.inst_decode // self.reg_file
        self.inst_decode // self.ctrl

        self.forward // self.scalar
        self.forward // self.matrix
        self.forward // self.vector
        self.forward // self.vector

        self.scalar // self.reg_file

        self.matrix // self.inst_decode
        self.vector // self.inst_decode
        self.transfer // self.inst_decode

        self.bus % self.matrix.matrix_buffer
        self.bus % self.vector.vector_buffer
        self.bus % self.transfer.transfer_buffer
        self.bus % self.buffer.buffer_port

        self.transfer.noc_interface % noc


    def initialize(self):
        pass
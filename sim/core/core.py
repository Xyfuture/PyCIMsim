from sim.config.config import CoreConfig
from sim.core.compo.base_core_compo import BaseCoreCompo
from sim.core.compo.local_buffer import LocalBuffer
from sim.core.compo.matrix import MatrixUnit
from sim.core.compo.message_bus import MessageBus
from sim.core.compo.transfer import TransferUnit
from sim.core.compo.vector import VectorUnit
from sim.core.compo.inst_fetch import InstFetch
from sim.core.compo.inst_decode import InstDecode, DecodeForward
from sim.core.compo.register_files import RegisterFiles
from sim.core.compo.scalar import ScalarUnit
from sim.core.compo.controller import Controller
from sim.network.simple.switch import Network


class Core(BaseCoreCompo):
    def __init__(self, sim, compo, core_id, noc: Network, config: CoreConfig, inst_buffer=None):
        super(Core, self).__init__(sim, compo)

        self._config = config
        self._inst_buffer = None
        self.core_id = core_id

        self.inst_fetch = InstFetch(sim, self, self._config)
        self.inst_decode = InstDecode(sim, self, self._config)
        self.forward = DecodeForward(sim, self)
        self.ctrl = Controller(sim, self)
        self.reg_file = RegisterFiles(sim, self, self._config)

        self.scalar = ScalarUnit(sim, self, self._config)
        self.vector = VectorUnit(sim, self, self._config)
        self.matrix = MatrixUnit(sim, self, self._config)
        self.transfer = TransferUnit(sim, self, self.core_id, self._config)

        self.bus = MessageBus(sim, self, self._config.local_bus)
        self.buffer = LocalBuffer(sim, self, self._config.local_buffer)

        self.inst_fetch // self.inst_decode
        self.inst_fetch // self.ctrl

        self.inst_decode // self.forward
        self.inst_decode // self.reg_file
        self.inst_decode // self.ctrl

        self.forward // self.scalar
        self.forward // self.matrix
        self.forward // self.vector
        self.forward // self.transfer

        self.scalar // self.reg_file

        self.matrix // self.inst_decode
        self.vector // self.inst_decode
        self.transfer // self.inst_decode

        self.bus % self.matrix.matrix_buffer
        self.bus % self.vector.vector_buffer
        self.bus % self.transfer.transfer_buffer
        self.bus % self.buffer.buffer_port

        self.transfer.noc_interface % noc

        if inst_buffer:
            self._inst_buffer = inst_buffer
            self.inst_fetch.set_inst_buffer(self._inst_buffer)

    def initialize(self):
        pass

    def set_inst_buffer(self, inst_buffer):
        self._inst_buffer = inst_buffer
        self.inst_fetch.set_inst_buffer(self._inst_buffer)

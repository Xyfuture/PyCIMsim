from sim.chip.memory.memory import Memory
from sim.config.config import ChipConfig
from sim.core.compo.base_core_compo import BaseCoreCompo
from sim.core.core import Core
from sim.des.base_compo import BaseCompo
from sim.network.simple.switch import Network


class Chip(BaseCompo):
    def __init__(self, sim, config: ChipConfig):
        super(Chip, self).__init__(sim)
        self.config = config

        self.inst_buffer_list = []

        self.core_list = []

        self.noc = Network(sim, self.config.noc_bus)

        self.global_memory = Memory(sim, 'global', self.config.global_memory)
        self.offchip_memory = Memory(sim, 'dram', self.config.offchip_memory)

        self.noc % self.global_memory.memory_port
        self.noc % self.offchip_memory.memory_port

        for i in range(self.config.core_cnt):
            self.core_list.append(
                Core(sim, i, self.noc, self.config.core_config)
            )

    def read_inst_buffer_list(self,inst_buffer_list):
        self.inst_buffer_list = inst_buffer_list
        for i,inst_buffer in enumerate(inst_buffer_list):
            self.core_list[i].set_inst_buffer(inst_buffer)

    def initialize(self):
        pass
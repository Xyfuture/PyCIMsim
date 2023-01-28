from collections import OrderedDict

from sim.chip.memory.memory import Memory
from sim.config.config import ChipConfig
from sim.core.compo.base_core_compo import BaseCoreCompo
from sim.core.core import Core
from sim.network.simple.switch import Network


class Chip(BaseCoreCompo):
    def __init__(self, sim, config: ChipConfig):
        super(Chip, self).__init__(sim, None)
        self.config = config

        self.inst_buffer_list = []

        self.core_list = []

        self.noc = Network(sim, self, self.config.noc_bus)

        self.global_memory = Memory(sim, self, 'global', self.config.global_memory)
        self.offchip_memory = Memory(sim, self, 'dram', self.config.offchip_memory)

        self.noc % self.global_memory.memory_port
        self.noc % self.offchip_memory.memory_port

        for i in range(self.config.core_cnt):
            self.core_list.append(
                Core(sim, self, i, self.noc, self.config.core_config)
            )

        self.running_status_dict = OrderedDict()

    def read_inst_buffer_list(self, inst_buffer_list):
        self.inst_buffer_list = inst_buffer_list
        for i, inst_buffer in enumerate(inst_buffer_list):
            self.core_list[i].set_inst_buffer(inst_buffer)
            print(f"core id:{i} len:{len(inst_buffer)}")

    def initialize(self):
        pass

    def get_running_status(self):
        for core in self.core_list:
            if not core.inst_fetch.is_finish():
                print(core.get_running_status())

    def log_running_status(self,core_id,status):
        self.running_status_dict[core_id] = status
        with open('./dump.txt','w') as f:
            f.write(str(self.running_status_dict))
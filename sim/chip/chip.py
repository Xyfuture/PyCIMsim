from sim.core.compo.base_core_compo import BaseCoreCompo
from sim.des.base_compo import BaseCompo


class Chip(BaseCompo):
    def __init__(self,sim,inst_path,config):
        super(Chip, self).__init__(sim)

        self.inst_buffer_list = []
        self.core_list = []


    def read_inst_buffer(self):
        pass


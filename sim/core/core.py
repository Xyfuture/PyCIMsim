from sim.des.base_compo import BaseCompo


class Core(BaseCompo):
    def __init__(self,sim,config=None):
        super(Core, self).__init__(sim)

    def initialize(self):
        pass
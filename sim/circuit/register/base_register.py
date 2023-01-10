from sim.des.base_compo import BaseCompo


class BaseRegister(BaseCompo):
    def __init__(self, sim, parent_compo):
        super(BaseRegister, self).__init__(sim, parent_compo)

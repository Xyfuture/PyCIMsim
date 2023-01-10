from __future__ import annotations

from sim.circuit.module.base_module import BaseModule


class BaseCoreCompo(BaseModule):
    def __init__(self, sim, compo):
        super(BaseCoreCompo, self).__init__(sim, compo)

    def get_running_status(self):
        pass

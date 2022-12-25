from __future__ import annotations

from sim.circuit.module.base_module import BaseModule
from sim.des.base_compo import BaseCompo
from sim.des.base_element import BaseElement
from sim.des.simulator import Simulator


class BaseCoreCompo(BaseModule):
    def __init__(self, sim):
        super(BaseCoreCompo, self).__init__(sim)


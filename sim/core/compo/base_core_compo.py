from __future__ import annotations

from sim.des.base_compo import BaseCompo
from sim.des.base_element import BaseElement
from sim.des.simulator import Simulator
from sim.core.utils.port.base_port import BasePort
from sim.core.utils.register.base_register import BaseRegister




class BaseCoreCompo(BaseCompo):
    def __init__(self, sim):
        super(BaseCoreCompo, self).__init__(sim)

        self._ports_dict = {}
        self._regs_dict = {}

        self._compos_dict = {}
        self._elements_dict = {}

    def __setattr__(self, key, value):
        # 注意优先级
        if isinstance(value, (BasePort)):
            self._ports_dict[key] = value
        elif isinstance(value, (BaseRegister)):
            self._compos_dict[key] = value

        elif isinstance(value, (BaseElement)):
            self._elements_dict[key] = value
        elif isinstance(value, (BaseCompo)):
            self._compos_dict[key] = value


        super(BaseCoreCompo, self).__setattr__(key, value)


    # 链接 port 专用
    def __floordiv__(self, other:BaseCoreCompo):
        for k in self._ports_dict:
            if k in other._ports_dict :
                self._ports_dict[k] // other._ports_dict[k]

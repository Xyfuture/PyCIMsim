from __future__ import annotations

from sim.circuit.register.base_register import BaseRegister
from sim.circuit.port.base_port import BasePort
from sim.circuit.port.port import UniReadPort, UniWritePort, UniWire
from sim.des.base_compo import BaseCompo
from sim.des.event import Event
from sim.des.base_element import BaseElement
from sim.des.stime import Stime
from sim.des.utils import fl


class BaseModule(BaseCompo):
    def __init__(self, sim):
        super(BaseModule, self).__init__(sim)

        self._input_wires_dict = {}
        self._output_wires_dict = {}
        self._inner_wires_dict = {}

        self._modules_dict = {}
        self._registers_dict = {}

        # self.registry_sensitive()

    def registry_sensitive(self):
        for method_name in dir(self):
            method = getattr(self,method_name)
            if callable(method) and hasattr(method, '_sensitive_list'):
                sen_list = method._sensitive_list
                # method = self.__dict__[method_name].__get__(None, self)
                for port_name in sen_list:
                    port = getattr(self,port_name)
                    port.add_callback(method)

    def __setattr__(self, key, value):
        if isinstance(value, UniReadPort):
            self._input_wires_dict[key] = value
        elif isinstance(value, UniWritePort):
            self._output_wires_dict[key] = value
        elif isinstance(value, UniWire):
            self._inner_wires_dict[key] = value
        elif isinstance(value, BaseRegister):
            self._registers_dict[key] = value
        elif isinstance(value, BaseModule):
            self._modules_dict[key] = value

        super(BaseModule, self).__setattr__(key, value)

    def __floordiv__(self, other: BaseModule):
        for k in self._input_wires_dict:
            if k in other._output_wires_dict:
                self._input_wires_dict[k] // other._output_wires_dict[k]

        for k in self._output_wires_dict:
            if k in other._input_wires_dict:
                self._output_wires_dict[k] // other._input_wires_dict[k]

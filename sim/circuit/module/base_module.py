from __future__ import annotations

from sim.circuit.register.base_register import BaseRegister

from sim.circuit.wire.base_wire import BaseWire
from sim.des.base_compo import BaseCompo
from sim.des.stime import Stime


class BaseModule(BaseCompo):
    def __init__(self, sim, compo):
        super(BaseModule, self).__init__(sim, compo)

        self._input_wires_dict = {}
        self._output_wires_dict = {}
        self._inner_wires_dict = {}

        # self._modules_dict = {}
        # self._registers_dict = {}

        # self.registry_sensitive()
        # 计算能耗
        self._static_energy = 0
        self._dynamic_energy = 0

        self._energy_logger = EnergyLogger(self)

    @property
    def total_energy(self):
        child_compo_energy = 0
        for compo in self._child_compo:
            if isinstance(compo,BaseModule):
                child_compo_energy += compo.total_energy
        return self._static_energy + self._dynamic_energy + child_compo_energy

    def circuit_add_dynamic_energy(self, energy):
        self._energy_logger.add_dynamic_energy(energy)

    def add_dynamic_energy(self, energy):
        self._dynamic_energy += energy

    def registry_sensitive(self):
        for method_name in dir(self):
            method = getattr(self, method_name)
            if callable(method) and hasattr(method, '_sensitive_list'):
                sen_list = method._sensitive_list
                # method = self.__dict__[method_name].__get__(None, self)
                for port_name in sen_list:
                    port = getattr(self, port_name)
                    port.add_callback(method)

    def __setattr__(self, key, value):
        if isinstance(value, BaseWire):
            if value.as_io_wire:
                if value.as_input:
                    self._input_wires_dict[key] = value
                elif value.as_output:
                    self._output_wires_dict[key] = value
            else:
                self._inner_wires_dict[key] = value

        # elif isinstance(value, BaseRegister):
        #     self._registers_dict[key] = value
        # elif isinstance(value, BaseModule):
        #     self._modules_dict[key] = value

        super(BaseModule, self).__setattr__(key, value)

    def __floordiv__(self, other: BaseModule):
        for k in self._input_wires_dict:
            if k in other._output_wires_dict:
                self._input_wires_dict[k] << other._output_wires_dict[k]

        for k in self._output_wires_dict:
            if k in other._input_wires_dict:
                self._output_wires_dict[k] >> other._input_wires_dict[k]


class EnergyLogger:
    def __init__(self,compo:BaseModule):
        self.last_record_time = Stime(0, 0)
        self.compo:BaseModule = compo

    def add_dynamic_energy(self,energy):
        if self.last_record_time.tick != self.compo.current_time.tick:
            self.compo.add_dynamic_energy(energy)
            self.last_record_time = self.compo.current_time


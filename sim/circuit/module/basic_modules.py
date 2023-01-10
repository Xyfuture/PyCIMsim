from __future__ import annotations

from sim.circuit.module.base_module import BaseModule
from sim.circuit.module.registry import registry

from sim.circuit.wire.wire import InWire, UniWire, OutWire, UniPulseWire
from sim.circuit.register.register import RegNext


class RegSustain(BaseModule):
    def __init__(self, sim,compo):
        super(RegSustain, self).__init__(sim,compo)

        self._data_reg = RegNext(sim,self)
        self._status_reg = RegNext(sim,self)

        self.data_input = InWire(UniWire,sim, self)
        self.output_wire = OutWire(UniWire,sim, self)
        self.status_input = InWire(UniWire,sim, self)  # IDLE for True BUSY for False

        # 内部端口
        self._data_reg_input = UniWire(sim,self)
        self._data_reg_output = UniWire(sim,self)
        self._status_reg_output = UniWire(sim,self)

        self._data_reg.connect(self._data_reg_input, self._data_reg_output)
        self._status_reg.connect(self.status_input, self._status_reg_output)

        self.registry_sensitive()

    def initialize(self):
        pass

    @registry(['data_input', 'status_input'])
    def handle_input(self):
        data_payload = self.data_input.read()
        status_payload = self.status_input.read()

        if status_payload:
            self._data_reg_input.write(data_payload)

    @registry(['_data_reg_output', '_status_reg_output'])
    def gen_output(self):
        payload = {'status': self._status_reg_output.read(), 'data_payload': self._data_reg_output.read()}
        self.output_wire.write(payload)

    def get_status_input_read_port(self):
        return self.status_input

    def connect(self, data_input: UniWire, status_input: UniWire, output: UniWire):
        self.data_input << data_input
        self.status_input << status_input
        self.output_wire >> output


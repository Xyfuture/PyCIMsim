from __future__ import annotations

from sim.circuit.module.base_module import BaseModule
from sim.circuit.module.registry import registry
from sim.circuit.register.base_register import BaseRegister
from sim.circuit.port.base_port import BasePort
from sim.circuit.port.port import UniReadPort, UniWritePort, UniWire
from sim.circuit.register.register import RegNext
from sim.des.base_compo import BaseCompo
from sim.des.event import Event
from sim.des.base_element import BaseElement
from sim.des.stime import Stime
from sim.des.utils import fl


class RegSustain(BaseModule):
    def __init__(self,sim):
        super(RegSustain, self).__init__(sim)

        self._data_reg = RegNext(self)
        self._status_reg = RegNext(self)

        self.data_input_read_port = UniReadPort(self)
        self.status_input_read_port = self._status_reg.get_input_read_port() # IDLE for True BUSY for False

        self.data_input_write_port = None
        self.status_input_write_port = None

        self._data_reg_input_write_port = self._data_reg.get_input_write_port()
        self._data_output_read_port = self._data_reg.get_output_read_port()
        self._status_output_read_port = self._status_reg.get_output_read_port()

        self.output_write_port = UniWritePort(self)
        self.output_read_port = None

        self.registry_sensitive()

    def initialize(self):
        pass

    @registry(['data_input_read_port','status_input_read_port'])
    def handle_input(self):
        data_payload = self.data_input_read_port.read()
        status_payload = self.status_input_read_port.read()

        if status_payload:
            self._data_reg_input_write_port.write(data_payload)

    @registry(['_data_output_read_port','_status_output_read_port'])
    def gen_output(self):
        payload = {'status':self._status_output_read_port.read(),'data_payload':self._data_output_read_port.read()}
        self.output_write_port.write(payload)

    def get_status_input_read_port(self):
        return self.status_input_read_port

    def get_status_input_write_port(self):
        self.status_input_write_port = UniWritePort(self)
        self.status_input_write_port // self.status_input_read_port
        return self.status_input_write_port

    def get_data_input_read_port(self):
        return self.data_input_read_port

    def get_data_input_write_port(self):
        self.data_input_write_port = UniWritePort(self)
        self.data_input_write_port // self.data_input_read_port
        return self.data_input_write_port

    def get_output_write_port(self):
        return self.output_write_port

    def get_output_read_port(self):
        self.output_read_port = UniReadPort(self)
        self.output_read_port // self.output_write_port
        return self.output_read_port




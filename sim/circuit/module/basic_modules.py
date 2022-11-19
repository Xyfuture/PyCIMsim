from __future__ import annotations

from sim.circuit.module.base_module import BaseModule
from sim.circuit.module.registry import registry
from sim.circuit.register.base_register import BaseRegister
from sim.circuit.port.base_port import BasePort
# from sim.circuit.port.port import UniReadPort, UniWritePort, UniWire
from sim.circuit.wire.wire import InWire, UniWire, OutWire, UniPulseWire
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

        self.data_input = InWire(UniWire,self)
        self.output_wire = OutWire(UniWire, self)
        self.status_input = InWire(UniWire,self) # IDLE for True BUSY for False

        # self.data_input_write_port = None
        # self.status_input_write_port = None

        self._data_reg_input = UniWire(self)
        self._data_reg_output = UniWire(self)
        self._status_reg_output = UniWire(self)

        self._data_reg.connect(self._data_reg_input,self._data_reg_output)
        self._status_reg.connect(self.status_input,self._status_reg_output)
        # self.output_read_port = None

        self.registry_sensitive()

    def initialize(self):
        pass

    @registry(['data_input','status_input'])
    def handle_input(self):
        data_payload = self.data_input.read()
        status_payload = self.status_input.read()

        if status_payload:
            self._data_reg_input.write(data_payload)

    @registry(['_data_reg_output','_status_reg_output'])
    def gen_output(self):
        payload = {'status':self._status_reg_output.read(), 'data_payload':self._data_reg_output.read()}
        self.output_wire.write(payload)

    def get_status_input_read_port(self):
        return self.status_input

    def connect(self,data_input:UniWire,status_input:UniWire,output:UniWire):
        self.data_input << data_input
        self.status_input << status_input
        self.output_wire >> output

    # def get_status_input_write_port(self):
    #     self.status_input_write_port = UniWritePort(self)
    #     self.status_input_write_port // self.status_input
    #     return self.status_input_write_port
    #
    # def get_data_input_read_port(self):
    #     return self.data_input
    #
    # def get_data_input_write_port(self):
    #     self.data_input_write_port = UniWritePort(self)
    #     self.data_input_write_port // self.data_input
    #     return self.data_input_write_port
    #
    # def get_output_write_port(self):
    #     return self.output_write_port
    #
    # def get_output_read_port(self):
    #     self.output_read_port = UniReadPort(self)
    #     self.output_read_port // self.output_write_port
    #     return self.output_read_port




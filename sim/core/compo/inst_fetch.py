from sim.circuit.module.registry import registry, registry_safe
from sim.circuit.register.register import RegEnable
# from sim.circuit.port.port import UniWritePort, UniReadPort
from sim.circuit.wire.wire import InWire, UniWire, OutWire, UniPulseWire
from sim.config.config import CoreConfig

from sim.core.compo.base_core_compo import BaseCoreCompo
from sim.des.simulator import Simulator
from sim.des.event import Event
from sim.des.base_compo import BaseCompo
from sim.des.stime import Stime


class InstFetch(BaseCoreCompo):
    def __init__(self, sim, config: CoreConfig):
        super(InstFetch, self).__init__(sim)
        self._config = config

        self._inst_buffer = []
        self._inst_buffer_len = 0

        self._pc_reg = RegEnable(self)

        self.jump_pc = InWire(UniWire, self)
        self.if_id_port = OutWire(UniWire, self)
        self.if_stall = OutWire(UniWire, self)
        self.if_enable = InWire(UniWire, self)

        self._pc_input = UniWire(self)
        self._pc_output = UniWire(self)

        self._pc_reg.connect(self._pc_input, self.if_enable, self._pc_output)

        self.registry_sensitive()

    @registry(['_pc_output', 'jump_pc'])
    def process(self):
        def fetch_inst():
            inst_payload = {'pc': pc, 'inst': self._inst_buffer[pc]}
            if jump_payload:
                inst_payload = {'pc': -1, 'inst': {'op': 'nop'}}
            self.if_id_port.write(inst_payload)

        def update_pc():
            next_pc = pc + 1
            # 如果这个周期内没发送jump,那么就不更新
            if jump_payload:
                next_pc = pc + jump_payload['offset']
            self._pc_input.write(next_pc)

        pc = self._pc_output.read()
        jump_payload = self.jump_pc.read()

        inst_payload = {'pc': -1, 'inst': {'op': 'nop'}}
        if pc < self._inst_buffer_len and not jump_payload:
            inst_payload = {'pc': pc, 'inst': self._inst_buffer[pc]}

        next_pc = pc + 1
        # 如果这个周期内没发送jump,那么就不更新
        if jump_payload:
            next_pc = pc + jump_payload['offset']

        if pc <= self._inst_buffer_len:
            self._pc_input.write(next_pc)
            self.if_id_port.write(inst_payload)

        # if 600 < pc < self._inst_buffer_len:
        #     self.get_running_status()

        if pc % 1000 == 0:
            print(pc)

        # if pc > 75000:
        #     self.get_running_status()

    def initialize(self):
        self._pc_reg.init(10)

        self.if_stall.write(False)
        self._pc_input.write(0)

        self.if_id_port.write(None)

    def set_inst_buffer(self, inst_buffer):
        self._inst_buffer = inst_buffer
        self._inst_buffer_len = len(self._inst_buffer)

    def get_running_status(self):
        print(f"InstFetch> pc:{self._pc_output.read()} inst:{self._inst_buffer[self._pc_output.read()]}")

from sim.circuit.module.base_module import EnergyLogger
from sim.circuit.module.registry import registry
from sim.circuit.register.register import RegEnable
from sim.circuit.wire.wire import InWire, UniWire, OutWire
from sim.config.config import CoreConfig
from sim.core.compo.base_core_compo import BaseCoreCompo


class InstFetch(BaseCoreCompo):
    def __init__(self, sim, compo, config: CoreConfig):
        super(InstFetch, self).__init__(sim, compo)
        self._config = config

        self._inst_buffer = []
        self._inst_buffer_len = 0

        self._pc_reg = RegEnable(sim, self)

        self.jump_pc = InWire(UniWire, sim, self)
        self.if_id_port = OutWire(UniWire, sim, self)
        self.if_stall = OutWire(UniWire, sim, self)
        self.if_enable = InWire(UniWire, sim, self)

        self._pc_input = UniWire(sim, self)
        self._pc_output = UniWire(sim, self)

        self._pc_reg.connect(self._pc_input, self.if_enable, self._pc_output)

        self.registry_sensitive()

    @registry(['_pc_output', 'jump_pc'])
    def process(self):
        pc = self._pc_output.read()
        jump_payload = self.jump_pc.read()

        inst_payload = {'pc': -1, 'inst': {'op': 'nop'}}
        if pc < self._inst_buffer_len and not jump_payload:
            inst_payload = {'pc': pc, 'inst': self._inst_buffer[pc]}

        next_pc = pc + 1
        # 如果这个周期内没发送jump,那么就不更新
        if jump_payload:
            next_pc = pc + jump_payload['offset']

        if pc < self._inst_buffer_len:
            self._pc_input.write(next_pc)
            self.if_id_port.write(inst_payload)
        else:
            self.if_id_port.write(None)

        if self.is_finish():
            core_id = 0
            if self._parent_compo:
                core_id = self._parent_compo.core_id
            print(f'Core id:{core_id} finish pc:{pc}')

        # 目前仅记录动态功耗，静态的可以直接算出来
        self.circuit_add_dynamic_energy(self._config.inst_fetch_energy)

        if __debug__:
            self.get_process(10000)

    def initialize(self):
        self.if_stall.write(False)
        self._pc_input.write(0)

        self.if_id_port.write(None)

    def set_inst_buffer(self, inst_buffer):
        self._inst_buffer = inst_buffer
        self._inst_buffer_len = len(self._inst_buffer)

    def get_running_status(self):
        core_id = 0
        if self._parent_compo:
            core_id = self._parent_compo.core_id
        if self.is_finish():
            return f"Core:{core_id} InstFetch> finish " \
                   f"pc:{self._pc_output.read()} len:{len(self._inst_buffer)}"

        info = f"Core:{core_id} InstFetch> " \
               f"pc:{self._pc_output.read()} inst:{self._inst_buffer[self._pc_output.read()]}"

        return info

    def is_finish(self):
        if self._pc_output.read() == len(self._inst_buffer):
            return True
        return False

    def get_process(self, interval=1000):
        if interval:  # not zero
            core_id = 0
            if self._parent_compo:
                core_id = self._parent_compo.core_id

            pc = self._pc_output.read()
            if pc % interval == 0:
                print(f"Core id:{core_id} pc:{pc} tick:{self.current_time}")

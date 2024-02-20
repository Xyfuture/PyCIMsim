from math import ceil
from typing import Optional

from sim.circuit.hybrid.trigger import Trigger
from sim.circuit.module.registry import registry
from sim.circuit.register.register import RegNext
from sim.config.config import CoreConfig
from sim.core.compo.base_core_compo import BaseCoreCompo
from sim.circuit.wire.wire import InWire, UniWire, OutWire
from sim.core.compo.connection.payloads import VectorInfo, BusPayload, MemoryRequest
from sim.core.compo.message_bus import MessageInterface
from sim.core.utils.payload.base import PayloadBase
from sim.core.utils.pfc import PerformanceCounter


class VectorFSMPayload(PayloadBase):
    vector_info: Optional[VectorInfo] = None
    status: Optional[str] = None  # idle or busy or finish


class VectorUnit(BaseCoreCompo):
    def __init__(self, sim, compo, config: CoreConfig):
        super(VectorUnit, self).__init__(sim, compo)

        self._config = config
        self.id_vector_port = InWire(UniWire, sim, self)

        self._fsm_reg = RegNext(sim, self)
        self._fsm_reg_input = UniWire(sim, self)
        self._fsm_reg_output = UniWire(sim, self)
        self._fsm_reg.connect(self._fsm_reg_input, self._fsm_reg_output)

        self.vector_buffer = MessageInterface(sim, self, 'vector')

        self.vector_busy = OutWire(UniWire, sim, self)

        self._finish_wire = UniWire(sim, self)

        self.func_trigger = Trigger(sim, self)

        self.registry_sensitive()

        if __debug__:
            self.pfc = PerformanceCounter(self)

    def initialize(self):
        self._fsm_reg.init(VectorFSMPayload(status='idle'))
        self._finish_wire.init(False)

        self.vector_busy.write(False)

    def calc_compute_latency(self, vector_info: VectorInfo):
        times = ceil(vector_info.len / self._config.vector_width)
        self.add_dynamic_energy(self._config.vector_energy * times)
        return self._config.vector_latency * times

    @registry(['_fsm_reg_output', '_finish_wire', 'id_vector_port'])
    def gen_fsm_input(self):
        fsm_payload: VectorFSMPayload = self._fsm_reg_output.read()
        old_vector_info, status = fsm_payload.vector_info, fsm_payload.status

        finish_info = self._finish_wire.read()

        new_vector_info: VectorInfo = self.id_vector_port.read()

        new_fsm_payload = fsm_payload

        if status == 'idle':
            if new_vector_info:
                new_fsm_payload = VectorFSMPayload(
                    status='busy', vector_info=new_vector_info
                )
        elif status == 'finish':
            if new_vector_info:
                new_fsm_payload = VectorFSMPayload(
                    status='busy', vector_info=new_vector_info
                )
            else:
                new_fsm_payload = VectorFSMPayload(status='idle')
        elif status == 'busy':
            if finish_info:
                new_fsm_payload = VectorFSMPayload(status='finish')
        else:
            assert False

        self._fsm_reg_input.write(new_fsm_payload)

    @registry(['_fsm_reg_output'])
    def process_fsm_output(self):
        fsm_payload = self._fsm_reg_output.read()
        vector_info, status = fsm_payload.vector_info, fsm_payload.status

        if status == 'idle':
            pass
        elif status == 'finish':
            stall_status = False
            self.vector_busy.write(stall_status)
            self._finish_wire.write(False) # reset
        elif status == 'busy':
            stall_status = True
            self.func_trigger.set()
            self.vector_busy.write(stall_status)
        else:
            assert False

    @registry(['func_trigger'])
    def process(self):

        if __debug__:
            self.pfc.begin()

        fsm_payload = self._fsm_reg_output.read()
        vector_info: VectorInfo = fsm_payload.vector_info

        input_vec_size = ceil(vector_info.len * self._config.input_precision / 8) * 2  # Bytes

        # 暂时设计为一次读出所有的结果
        memory_read_request = BusPayload(
            src='vector', dst='buffer', data_size=1,  # 是请求的大小,不是实际数据大小
            payload=MemoryRequest(access_type='read', data_size=input_vec_size)
        )

        self.vector_buffer.send(memory_read_request, None)

    @registry(['vector_buffer'])
    def execute_vector(self, payload):
        vector_info: VectorInfo = self._fsm_reg_output.read().vector_info
        latency = self.calc_compute_latency(vector_info)

        output_vec_size = ceil(vector_info.len * self._config.input_precision / 8)  # Bytes
        memory_write_request = BusPayload(
            src='vector', dst='buffer', data_size=output_vec_size,
            payload=MemoryRequest(access_type='write', data_size=output_vec_size)
        )
        f = lambda: self.vector_buffer.send(memory_write_request, self.finish_execute)

        self.make_event(f, self.current_time + latency)

    def finish_execute(self):
        if __debug__:
            self.pfc.finish()

        self.vector_buffer.allow_receive()
        self._finish_wire.write(True)

    def get_running_status(self):
        core_id = 0
        if self._parent_compo:
            core_id = self._parent_compo.core_id

        fsm_info = self._fsm_reg_output.read()
        info = f"Core:{core_id} VectorUnit> {fsm_info}"
        return info

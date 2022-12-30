from math import ceil

from sim.circuit.module.basic_modules import RegSustain
from sim.circuit.module.registry import registry
from sim.circuit.register.register import Trigger
from sim.config.config import CoreConfig
from sim.core.compo.base_core_compo import BaseCoreCompo
from sim.circuit.wire.wire import InWire, UniWire, OutWire, UniPulseWire
from sim.core.compo.connection.payloads import VectorInfo, BusPayload, MemoryRequest
from sim.core.compo.message_bus import MessageInterface


class VectorUnit(BaseCoreCompo):
    def __init__(self,sim,config:CoreConfig):
        super(VectorUnit, self).__init__(sim)

        self._config = config
        self.id_vector_port = InWire(UniWire,self)

        self._reg_head = RegSustain(sim)
        self._status_input = UniWire(self)
        self._reg_head_output = UniWire(self)
        self._reg_head.connect(self.id_vector_port,self._status_input,self._reg_head_output)

        self.vector_buffer = MessageInterface(self,'vector')

        self.vector_busy = OutWire(UniWire,self)

        self.finish_wire = UniPulseWire(self)

        self.func_trigger = Trigger(self)
        self.trigger_input = UniPulseWire(self)
        self.func_trigger.connect(self.trigger_input)

        self.registry_sensitive()

    def initialize(self):
        self._status_input.write(True)

    def calc_compute_latency(self,vector_info:VectorInfo):
        if self._config:
            times = ceil(vector_info.vec_len / self._config.vector_width)
            self.add_dynamic_energy(self._config.vector_energy * times)
            return self._config.vector_latency*times
        else:
            return 10

    @registry(['_reg_head_output','finish_wire'])
    def check_stall_status(self):
        reg_head_payload = self._reg_head_output.read()
        finish_info = self.finish_wire.read()

        data_payload,idle = reg_head_payload['data_payload'],reg_head_payload['status']

        new_idle_status = True
        trigger_status = False
        stall_status = False

        if idle:
            if data_payload:
                if data_payload['ex'] == 'matrix':
                    new_idle_status = False
                    trigger_status = True
                    stall_status = True
        else:
            if finish_info:
                new_idle_status = True
                trigger_status = False
                stall_status = False
            else:
                new_idle_status = False
                trigger_status = False
                stall_status = True

        self._status_input.write(new_idle_status)
        self.trigger_input.write(trigger_status)
        self.vector_busy.write(stall_status)

    @registry(['func_trigger'])
    def process(self):
        decode_payload = self._reg_head_output.read()

        if not decode_payload:
            return

        vector_info:VectorInfo = decode_payload['data_payload']
        input_vec_size =  ceil(vector_info.vec_len * self._config.input_precision /8) *2 # Bytes

        # 暂时设计为一次读出所有的结果
        memory_read_request = BusPayload(
            src='vector',dst='buffer',data_size=1, # 是请求的大小,不是实际数据大小
            payload = MemoryRequest(access_type='read',data_size=input_vec_size)
        )

        self.vector_buffer.send(memory_read_request, None)

    @registry(['vector_buffer'])
    def execute_vector(self, payload):
        vector_info:VectorInfo = self._reg_head_output.read()['data_payload']
        latency = self.calc_compute_latency(vector_info)

        output_vec_size = ceil(vector_info.vec_len * self._config.input_precision / 8) # Bytes
        memory_write_request = BusPayload(
            src='vector',dst='buffer',data_size=output_vec_size,
            payload = MemoryRequest(access_type='write',data_size=output_vec_size)
        )
        f = lambda: self.vector_buffer.send(memory_write_request, self.finish_execute)

        self.make_event(f, self.current_time + latency)

    def finish_execute(self):
        # print("finish vector time:{}".format(self.current_time))

        self.vector_buffer.allow_receive()
        self.finish_wire.write(True)



from math import ceil

from sim.circuit.module.basic_modules import RegSustain
from sim.circuit.module.registry import registry
# from sim.circuit.port.port import UniReadPort, UniWritePort, UniPulseWire
from sim.circuit.wire.wire import InWire, UniWire, OutWire, UniPulseWire
from sim.circuit.register.register import RegNext, Trigger
from sim.config.config import CoreConfig
from sim.core.compo.base_core_compo import BaseCoreCompo
from sim.core.compo.connection.payloads import MatrixInfo, MemoryRequest, MemoryReadValue, BusPayload

from sim.core.compo.message_bus import MessageInterface


class MatrixUnit(BaseCoreCompo):
    def __init__(self, sim, config: CoreConfig = None):
        super(MatrixUnit, self).__init__(sim)
        self._config = config

        self.id_matrix_port = InWire(UniWire, self)

        self._reg_head = RegSustain(sim)
        self._status_input = UniWire(self)
        self._reg_head_output = UniWire(self)
        self._reg_head.connect(self.id_matrix_port, self._status_input, self._reg_head_output)

        self.matrix_buffer = MessageInterface(self, 'matrix')

        self.matrix_busy = OutWire(UniWire, self)

        self.finish_wire = UniPulseWire(self)

        self.func_trigger = Trigger(self)
        self.trigger_input = UniPulseWire(self)
        self.func_trigger.connect(self.trigger_input)

        self.registry_sensitive()

    def initialize(self):
        self._status_input.write(True)

    def calc_compute_latency(self, matrix_info:MatrixInfo):
        if self._config:
            pe_num = matrix_info.pe_assign[1][0] * matrix_info.pe_assign[1][1]
            self.add_dynamic_energy(self._config.matrix_energy_per_pe * pe_num)
            return self._config.matrix_latency
        else:
            return 1000

    @registry(['_reg_head_output', 'finish_wire'])
    def check_stall_status(self):
        reg_head_payload = self._reg_head_output.read()
        finish_info = self.finish_wire.read()

        data_payload, idle = reg_head_payload['data_payload'], reg_head_payload['status']

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
        self.matrix_busy.write(stall_status)

    @registry(['func_trigger'])
    def process(self):
        decode_payload = self._reg_head_output.read()

        if not decode_payload:
            return

        matrix_info: MatrixInfo = decode_payload['data_payload']

        # 计算需要的数据量
        input_vec_size = ceil(matrix_info.pe_assign[1][0] * self._config.xbar_size[0]
                              * self._config.input_precision / 8)  # Bytes not bits

        # memory_read_request = {'src': 'matrix', 'dst': 'buffer', 'data_size': 128, 'access_type': 'read'}
        memory_read_request = BusPayload(
            src='matrix', dst='buffer', data_size=1, # 是请求的大小
            payload=MemoryRequest(access_type='read', addr=matrix_info.vec_addr, data_size=input_vec_size)
        )

        self.matrix_buffer.send(memory_read_request, None)

    @registry(['matrix_buffer'])
    def execute_gemv(self, payload):
        matrix_info: MatrixInfo = self._reg_head_output.read()['data_payload']
        output_vec_size = ceil(matrix_info.pe_assign[1][1] * self._config.xbar_size[1] * self._config.device_precision
                               * (self._config.input_precision / 8) / self._config.weight_precision)  # Bytes

        latency = self.calc_compute_latency(matrix_info)
        # memory_write_request = {'src': 'matrix', 'dst': 'buffer', 'data_size': 128, 'access_type': 'write'}

        memory_write_request = BusPayload(
            src='matrix', dst='buffer', data_size=output_vec_size,
            payload=MemoryRequest(access_type='write', data_size=output_vec_size, addr=matrix_info.out_addr)
        )

        f = lambda: self.matrix_buffer.send(memory_write_request, self.finish_execute)

        self.make_event(f, self.current_time + latency)

    def finish_execute(self):
        # print("finish gemv time:{}".format(self.current_time))

        self.matrix_buffer.allow_receive()
        self.finish_wire.write(True)

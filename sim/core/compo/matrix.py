from math import ceil
from typing import Optional

from sim.circuit.hybrid.trigger import Trigger
from sim.circuit.module.registry import registry
from sim.circuit.wire.wire import InWire, UniWire, OutWire
from sim.circuit.register.register import RegNext
from sim.config.config import CoreConfig
from sim.core.compo.base_core_compo import BaseCoreCompo
from sim.core.compo.connection.payloads import MatrixInfo, MemoryRequest, BusPayload

from sim.core.compo.message_bus import MessageInterface
from sim.core.utils.payload.base import PayloadBase
from sim.core.utils.pfc import PerformanceCounter


class MatrixFSMPayload(PayloadBase):
    matrix_info: Optional[MatrixInfo] = None
    status: Optional[str] = None  # idle or busy or finish(just finish)


class MatrixUnit(BaseCoreCompo):
    def __init__(self, sim, compo, config: CoreConfig):
        super(MatrixUnit, self).__init__(sim, compo)
        self._config = config

        self.id_matrix_port = InWire(UniWire, sim, self)

        self._fsm_reg = RegNext(sim, self)
        self._fsm_reg_input = UniWire(sim, self)
        self._fsm_reg_output = UniWire(sim, self)
        self._fsm_reg.connect(self._fsm_reg_input, self._fsm_reg_output)

        self.matrix_buffer = MessageInterface(sim, self, 'matrix')

        self.matrix_busy = OutWire(UniWire, sim, self)

        self._finish_wire = UniWire(sim, self)

        self.func_trigger = Trigger(sim, self)

        self.registry_sensitive()

        if __debug__:
            self.pfc = PerformanceCounter(self)

    def initialize(self):
        self._fsm_reg.init(MatrixFSMPayload(  # 初始化为None会报错，需要初始化为MatrixFSMPayload
            matrix_info=None, status='idle'
        ))
        self._finish_wire.init(False)

        self.matrix_busy.write(False)

    def calc_compute_latency(self, matrix_info: MatrixInfo):
        pe_num = matrix_info.pe_assign[1][0] * matrix_info.pe_assign[1][1]
        self.add_dynamic_energy(self._config.matrix_energy_per_pe * pe_num)
        return self._config.matrix_latency


    @registry(['_fsm_reg_output', '_finish_wire', 'id_matrix_port'])
    def gen_fsm_input(self):
        fsm_payload: MatrixFSMPayload = self._fsm_reg_output.read()
        old_matrix_info, status = fsm_payload.matrix_info, fsm_payload.status

        finish_info = self._finish_wire.read()

        new_matrix_info: MatrixInfo = self.id_matrix_port.read()

        new_fsm_payload = fsm_payload
        if status == 'idle':
            if new_matrix_info:
                new_fsm_payload = MatrixFSMPayload(
                    status='busy', matrix_info=new_matrix_info
                )
        elif status == 'finish':
            if new_matrix_info:
                new_fsm_payload = MatrixFSMPayload(
                    status='busy', matrix_info=new_matrix_info
                )
            else:
                new_fsm_payload = MatrixFSMPayload(status='idle')
        elif status == 'busy':
            if finish_info:  # True for finish work
                new_fsm_payload = MatrixFSMPayload(status='finish')
        else:
            assert False

        # 输出到状态机的寄存器中，如果没变化不输出（没实现__eq__,不确定比较结果）
        self._fsm_reg_input.write(new_fsm_payload)

    @registry(['_fsm_reg_output'])
    def process_fsm_output(self):
        fsm_payload = self._fsm_reg_output.read()
        matrix_info, status = fsm_payload.matrix_info, fsm_payload.status

        stall_status = False
        if status == 'idle':
            pass
        elif status == 'finish':
            stall_status = False
            self.matrix_busy.write(stall_status)
            self._finish_wire.write(False)  # 手动关闭
        elif status == 'busy':
            # print(f"gemv start tick:{self.current_time}")
            stall_status = True
            self.func_trigger.set()
            self.matrix_busy.write(stall_status)
        else:
            assert False
        # 暂时较为简陋

    @registry(['func_trigger'])
    def process(self):

        if __debug__:
            self.pfc.begin()

        fsm_payload = self._fsm_reg_output.read()
        matrix_info: MatrixInfo = fsm_payload.matrix_info

        # 计算需要的数据量
        input_vec_size = ceil(matrix_info.pe_assign[1][0] * self._config.xbar_size[0]
                              * self._config.input_precision / 8)  # Bytes not bits

        # memory_read_request = {'src': 'matrix', 'dst': 'buffer', 'data_size': 128, 'access_type': 'read'}
        memory_read_request = BusPayload(
            src='matrix', dst='buffer', data_size=1,  # 是请求的大小
            payload=MemoryRequest(access_type='read', addr=matrix_info.vec_addr, data_size=input_vec_size)
        )

        self.matrix_buffer.send(memory_read_request, None)

    @registry(['matrix_buffer'])
    def execute_gemv(self, payload):
        matrix_info: MatrixInfo = self._fsm_reg_output.read().matrix_info

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
        if __debug__:
            self.pfc.finish()

        self.matrix_buffer.allow_receive()
        self._finish_wire.write(True)

    def get_running_status(self):
        core_id = 0
        if self._parent_compo:
            core_id = self._parent_compo.core_id

        fsm_info = self._fsm_reg_output.read()
        info = f"Core:{core_id} MatrixUnit> {fsm_info}"
        return info

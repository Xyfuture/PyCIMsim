from typing import Optional

from sim.circuit.hybrid.trigger import Trigger
from sim.circuit.module.registry import registry
from sim.circuit.wire.wire import InWire, UniWire, OutWire
from sim.circuit.register.register import RegNext
from sim.config.config import CoreConfig
from sim.core.compo.base_core_compo import BaseCoreCompo
from sim.core.compo.connection.payloads import TransferInfo, BusPayload, MemoryRequest, SyncMessage

from sim.core.compo.message_bus import MessageInterface
from sim.core.utils.payload.base import PayloadBase
from sim.des.stime import Stime
from sim.network.simple.switch import SwitchInterface


class TransferFSMPayload(PayloadBase):
    transfer_info: Optional[TransferInfo] = None
    status: Optional[str] = None  # idle busy finish(just finish before idle)


class TransferUnit(BaseCoreCompo):
    def __init__(self, sim, compo, core_id, config: CoreConfig):
        super(TransferUnit, self).__init__(sim, compo)
        self._config = config
        self.core_id = core_id

        self.id_transfer_port = InWire(UniWire, sim, self)

        self._fsm_reg = RegNext(sim, self)
        self._fsm_reg_input = UniWire(sim, self)
        self._fsm_reg_output = UniWire(sim, self)
        self._fsm_reg.connect(self._fsm_reg_input, self._fsm_reg_output)

        self.transfer_buffer = MessageInterface(sim, self, 'transfer')

        self.transfer_busy = OutWire(UniWire, sim, self)

        self._finish_wire = UniWire(sim, self)

        self.func_trigger = Trigger(sim, self)

        self.noc_interface = SwitchInterface(sim, self, core_id)

        self._run_state = 'idle'

        self.sync_dict = {}  # 同步的状态 对于master core而言
        self.is_sync_master_core = False

        self.state_value = 0
        self.wait_core_dict = {}  # core_id:value 其他核等待本核

        self.registry_sensitive()

    def initialize(self):
        self._fsm_reg.init(TransferFSMPayload(status='idle'))
        self._finish_wire.init(False)

        self.transfer_busy.write(False)

    def calc_compute_latency(self, payload):
        return 10

    @registry(['_fsm_reg_output', '_finish_wire', 'id_transfer_port'])
    def gen_fsm_input(self):
        fsm_payload: TransferFSMPayload = self._fsm_reg_output.read()
        old_transfer_info, status = fsm_payload.transfer_info, fsm_payload.status

        finish_info = self._finish_wire.read()

        new_transfer_info: TransferInfo = self.id_transfer_port.read()

        new_fsm_payload = fsm_payload
        if status == 'idle':
            if new_transfer_info:
                new_fsm_payload = TransferFSMPayload(
                    status='busy', transfer_info=new_transfer_info
                )
        elif status == 'finish':
            if new_transfer_info:
                new_fsm_payload = TransferFSMPayload(
                    status='busy', transfer_info=new_transfer_info
                )
            else:
                new_fsm_payload = TransferFSMPayload(status='idle')
        elif status == 'busy':
            if finish_info:
                new_fsm_payload = TransferFSMPayload(status='finish')
        else:
            assert False

        # if self.core_id == 12:
        #     print('in gen fsm input>\n' + f'time:{self.current_time}\n' +
        #           f'old fsm:{fsm_payload}\n' +
        #           f'id_transfer_port:{new_transfer_info}\n' +
        #           f'new fsm:{new_fsm_payload}')
        #
        #     # if self.current_time == Stime(570880,23):
        #     #     print('here')
        #
        #     # if self.current_time == Stime(570881,3):
        #     print(f'input wire> read {self._fsm_reg_input.force_read()}\n'+
        #           f'reg> \n'
        #           f'current_payload: {self._fsm_reg._payload}\n'+
        #           f'update_time: {self._fsm_reg._update_time}\n')
        self._fsm_reg_input.write(new_fsm_payload)

    @registry(['_fsm_reg_output'])
    def process_fsm_output(self):
        fsm_payload = self._fsm_reg_output.read()
        transfer_info, status = fsm_payload.transfer_info, fsm_payload.status

        if status == 'idle':
            pass
        elif status == 'finish':
            self.transfer_busy.write(False)
            self._finish_wire.write(False)
        elif status == 'busy':
            self.func_trigger.set()
            self.transfer_busy.write(True)
        else:
            assert False

    # local_buffer receive
    @registry(['transfer_buffer'])
    def local_buffer_receive_dispatch(self, bus_payload: BusPayload):
        self.memory_receive_handler(bus_payload)
        self.transfer_buffer.allow_receive()  # 暂时在这里接收

    @registry(['noc_interface'])
    def noc_receive_dispatch(self, bus_payload: BusPayload):
        payload = bus_payload.payload
        if isinstance(payload, SyncMessage):
            if payload.op == 'sync':
                self.sync_receive_handler(bus_payload)
            elif payload.op == 'wait_core':  # 其他节点等待本节点
                self.wait_core_receive_handler(bus_payload)
            elif payload.op == 'inc_state':  # 本节点等待完成
                self.inc_state_receive_handler(bus_payload)
        else:
            self.memory_receive_handler(bus_payload)
            self.noc_interface.allow_receive()  # 暂时在这里接受

    # 发射指令
    @registry(['func_trigger'])
    def process(self):
        # reg_head_payload = self._reg_head_output.read()
        # data_payload = reg_head_payload['data_payload']
        transfer_info: TransferInfo = self._fsm_reg_output.read().transfer_info

        op = transfer_info.op
        self._run_state = op

        # if self.core_id == 12:
        #     print(self._parent_compo.get_running_status())

        if op == 'sync':
            self.execute_sync(transfer_info)
        elif op == 'wait_core':
            self.execute_wait_core(transfer_info)
        elif op == 'inc_state':
            self.execute_inc_state(transfer_info)
        else:
            self.execute_memory(transfer_info)

        self.circuit_add_dynamic_energy(self._config.transfer_energy)

    def execute_sync(self, transfer_info: TransferInfo):
        start_core, end_core = transfer_info.sync_info['start_core'], transfer_info.sync_info['end_core']
        self.is_sync_master_core = (start_core == self.core_id)

        if self.is_sync_master_core:
            if start_core == end_core:
                self.is_sync_master_core = False
                self.finish_execute()
            else:
                for core in range(start_core + 1, end_core + 1):
                    self.sync_dict[core] = False
                for core in self.sync_dict:
                    query_sync_request = BusPayload(
                        src=self.core_id, dst=core, data_size=1,
                        payload=SyncMessage(
                            op='sync', message='query'
                        )
                    )
                    self.noc_interface.send(query_sync_request, None)
        else:
            self.slave_core_start_sync()

    def master_core_check_finsh(self):
        for k, v in self.sync_dict.items():
            if not v:
                return False
        return True

    def master_core_finish_sync(self):
        for core in self.sync_dict:
            finish_sync_request = BusPayload(
                src=self.core_id, dst=core,data_size=1,
                payload=SyncMessage(
                    op='sync', message='finish'
                )
            )
            self.noc_interface.send(finish_sync_request, None)

    def slave_core_start_sync(self):
        transfer_info: TransferInfo = self._fsm_reg_output.read().transfer_info
        master_core = transfer_info.sync_info.start_core
        start_sync_request = BusPayload(
            src=self.core_id, dst=master_core, data_size=1,
            payload=SyncMessage(
                op='sync', message='start'
            )
        )
        self.noc_interface.send(start_sync_request, None)

    # 处理所有与sync有关的信息,不论目前是什么状态
    def sync_receive_handler(self, bus_payload: BusPayload):
        if self._run_state == 'sync':
            sync_message: SyncMessage = bus_payload.payload
            if sync_message.message == 'start':
                if self.is_sync_master_core:
                    src = bus_payload.src
                    self.sync_dict[src] = True

                    if self.master_core_check_finsh():  # finish
                        self.master_core_finish_sync()
                        self.sync_dict = {}
                        self.finish_execute()
                        self.is_sync_master_core = False

            elif sync_message.message == 'finish':
                self.finish_execute()
            elif sync_message.message == 'query':
                self.slave_core_start_sync()
        self.noc_interface.allow_receive()

    def execute_wait_core(self, transfer_info: TransferInfo):

        start_wait_core_request = BusPayload(
            src=self.core_id, dst=transfer_info.sync_info['core_id'], data_size=1,
            payload=SyncMessage(
                op='wait_core', message='start', state=transfer_info.sync_info['state']
            )
        )

        self.noc_interface.send(start_wait_core_request, None)

    # 处理所有与wait_core有关的信息,不论目前是什么状态
    def wait_core_receive_handler(self, bus_payload: BusPayload):
        sync_message: SyncMessage = bus_payload.payload
        assert sync_message.message == 'start'
        if sync_message.message == 'start':
            # 其他核开始等待本核
            state = sync_message.state  # 等待本核的state
            if self.state_value >= state:
                finish_wait_core_request = BusPayload(
                    src=self.core_id, dst=bus_payload.src, data_size=1,
                    payload=SyncMessage(
                        op='inc_state', message='finish', state=self.state_value
                    )
                )
                self.noc_interface.send(finish_wait_core_request, None)
            else:
                self.wait_core_dict[bus_payload.src] = state

        self.noc_interface.allow_receive()

    def execute_inc_state(self, transfer_info):
        self.state_value += 1

        finish_list = []
        for k, v in self.wait_core_dict.items():
            if v <= self.state_value:
                finish_list.append(k)

        for k in finish_list:
            finish_wait_core_request = BusPayload(
                src=self.core_id, dst=k, data_size=1,
                payload=SyncMessage(
                    op='inc_state', message='finish', state=self.state_value
                )
            )

            self.noc_interface.send(finish_wait_core_request, None)
            del self.wait_core_dict[k]

        self.make_event(self.finish_execute, self.current_time + 1)

    def inc_state_receive_handler(self, bus_payload: BusPayload):
        sync_message: SyncMessage = bus_payload.payload
        assert sync_message.message == 'finish'
        if sync_message.message == 'finish':
            assert self._run_state == 'wait_core'
            self.finish_execute()
        self.noc_interface.allow_receive()

    def execute_memory(self, transfer_info: TransferInfo):

        op = transfer_info.op
        if op == 'dram_to_global':
            dram_read_reqeust = BusPayload(
                src=self.core_id, dst='dram', data_size=1,
                payload=MemoryRequest(
                    access_type='read', addr=transfer_info.mem_access_info.src_addr,
                    data_size=transfer_info.mem_access_info.data_size
                )
            )
            self.noc_interface.send(dram_read_reqeust, None)
        elif op in ['global_to_local', 'global_to_dram', 'global_cpy']:
            global_read_reqeust = BusPayload(
                src=self.core_id, dst='global', data_size=1,
                payload=MemoryRequest(
                    access_type='read', addr=transfer_info.mem_access_info.src_addr,
                    data_size=transfer_info.mem_access_info.data_size
                )
            )
            self.noc_interface.send(global_read_reqeust, None)
        elif op in ['local_to_global', 'local_cpy']:
            local_read_request = BusPayload(
                src='transfer', dst='buffer', data_size=1,
                payload=MemoryRequest(
                    access_type='read', addr=transfer_info.mem_access_info.src_addr,
                    data_size=transfer_info.mem_access_info.data_size
                )
            )
            self.transfer_buffer.send(local_read_request, None)
        elif op == 'global_clr':
            global_write_request = BusPayload(
                src=self.core_id, dst='global', data_size=transfer_info.mem_access_info.data_size,
                payload=MemoryRequest(
                    access_type='write', addr=transfer_info.mem_access_info.src_addr,
                    data_size=transfer_info.mem_access_info.data_size
                )
            )
            self.noc_interface.send(global_write_request, self.finish_execute)
        elif op == 'local_clr':
            local_write_request = BusPayload(
                src='transfer', dst='buffer', data_size=transfer_info.mem_access_info.data_size,
                payload=MemoryRequest(
                    access_type='write', addr=transfer_info.mem_access_info.src_addr,
                    data_size=transfer_info.mem_access_info.data_size
                )
            )
            self.transfer_buffer.send(local_write_request, self.finish_execute)

    def memory_receive_handler(self, bus_payload: BusPayload):
        # 第二次执行时的操作,读取的数据到了,转发到第二个
        fsm_payload = self._fsm_reg_output.read()
        transfer_info: TransferInfo = fsm_payload.transfer_info

        op = transfer_info.op
        if op in ['global_to_local', 'local_cpy']:
            local_write_request = BusPayload(
                src='transfer', dst='buffer', data_size=transfer_info.mem_access_info.data_size,
                payload=MemoryRequest(
                    access_type='write', addr=transfer_info.mem_access_info.dst_addr,
                    data_size=transfer_info.mem_access_info.data_size
                )
            )
            self.transfer_buffer.send(local_write_request, self.finish_execute)
        elif op in ['dram_to_global', 'local_to_global', 'global_cpy']:
            global_write_request = BusPayload(
                src=self.core_id, dst='global', data_size=transfer_info.mem_access_info.data_size,
                payload=MemoryRequest(
                    access_type='write', addr=transfer_info.mem_access_info.dst_addr,
                    data_size=transfer_info.mem_access_info.data_size
                )
            )
            self.noc_interface.send(global_write_request, self.finish_execute)
        elif op == 'global_to_dram':
            dram_write_request = BusPayload(
                src=self.core_id, dst='dram', data_size=transfer_info.mem_access_info.data_size,
                payload=MemoryRequest(
                    access_type='write', addr=transfer_info.mem_access_info.dst_addr,
                    data_size=transfer_info.mem_access_info.data_size
                )
            )
            self.noc_interface.send(dram_write_request, self.finish_execute)
        else:
            assert False

    def finish_execute(self):
        # print("core_id:{} finish sync".format(self.core_id))
        self._run_state = 'idle'
        self._finish_wire.write(True)

    def get_running_status(self):
        core_id = 0
        if self._parent_compo:
            core_id = self._parent_compo.core_id

        fsm_info = self._fsm_reg_output.read()
        info = f"Core:{core_id} TransferUnit> {fsm_info}"
        return info

# 一些格式信息
# {'src':1,'dst':2,'data_size':1,'op':'sync','message':'start/finish','sync_cnt':sync_cnt}
# {'src':1,'dst':2,'data_size':1,'op':'wait_core','message':'finish','state':self.state_value}
# {'src':1,'dst':2,'data_size':1,'op':'wait_core','message':'start','state':self.wait_state}

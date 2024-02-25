from typing import Optional, Union, Generator

from sim.circuit.hybrid.trigger import Trigger
from sim.circuit.module.registry import registry
from sim.circuit.wire.wire import InWire, UniWire, OutWire
from sim.circuit.register.register import RegNext
from sim.config.config import CoreConfig
from sim.core.compo.base_core_compo import BaseCoreCompo
from sim.core.compo.connection.payloads import TransferInfo, BusPayload, MemoryRequest, SyncMessage, InterCoreMessage

from sim.core.compo.message_bus import MessageInterface
from sim.core.utils.payload.base import PayloadBase
from sim.core.utils.pfc import PerformanceCounter
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

        self.recv_waiting_sender_dict = {}

        self.cur_send_coroutine: Union[Generator, None] = None
        self.cur_recv_coroutine: Union[Generator, None] = None
        self.cur_memory_coroutine: Union[Generator, None] = None

        self.registry_sensitive()

        if __debug__:
            self.pfc = PerformanceCounter(self)

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
        transfer_info: TransferInfo = self._fsm_reg_output.read().transfer_info

        op = transfer_info.op
        self._run_state = op

        if __debug__:
            self.pfc.begin(op)

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
                src=self.core_id, dst=core, data_size=1,
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

        if __debug__:
            self.pfc.finish(self._run_state)

        self._run_state = 'idle'
        self._finish_wire.write(True)

    def process_send(self, transfer_info: TransferInfo):
        op = transfer_info.op
        assert op == 'send'

        receiver_core_id = transfer_info.imm

        sender_ready_request = BusPayload(
            src=self.core_id, dst=receiver_core_id, data_size=1,
            payload=InterCoreMessage(
                sender_id=self.core_id, receiver_id=receiver_core_id,
                is_sender=True, status='sender_ready'
            )
        )
        self.noc_interface.send(sender_ready_request, None)

        yield ('sender ready req send,'
               'wait for receiver ready')

        # 读取本地内存
        local_read_request = BusPayload(
            src='transfer', dst='buffer', data_size=transfer_info.len,
            payload=MemoryRequest(
                access_type='read', addr=transfer_info.src1_addr,
                data_size=transfer_info.len,
            )
        )
        self.transfer_buffer.send(local_read_request, None)

        yield ('read local memory req send'
               'wait for read finish')

        # 发送数据到其他核心
        send_data_request = BusPayload(
            src=self.core_id, dst=receiver_core_id, data_size=transfer_info.len,
            payload=InterCoreMessage(
                sender_id=self.core_id, receiver_id=receiver_core_id,
                is_sender=True, status='send_data'
            )
        )

        self.noc_interface.send(send_data_request, self.finish_execute)

    def noc_send_handler(self, transfer_info: TransferInfo, bus_payload: BusPayload):
        inter_core_message: InterCoreMessage = bus_payload.payload

        sender_core_id, receiver_core_id = inter_core_message.sender_id, inter_core_message.receiver_id
        assert sender_core_id == self.core_id
        assert receiver_core_id == transfer_info.imm

        # 检查receiver是正确的，并已经就绪，切换回 process send进程
        if receiver_core_id == transfer_info.imm and \
                inter_core_message.status == 'receiver_ready':

            next(self.cur_send_coroutine)
        else:
            assert False

    def process_receive(self, transfer_info: TransferInfo):
        #TODO 有bug 关于 allow receive的

        op = transfer_info.op
        assert op == 'recv'

        sender_core_id = transfer_info.imm

        if sender_core_id in self.recv_waiting_sender_dict:
            # sender 已经在等待receiver 了，直接发送 receiver ready 信号
            receiver_ready_request = BusPayload(
                src=self.core_id, dst=sender_core_id, data_size=transfer_info.len,
                payload=InterCoreMessage(
                    sender_id=sender_core_id, receiver_id=self.core_id,
                    is_sender=False, status='receiver_ready'
                )
            )

            del self.recv_waiting_sender_dict[sender_core_id]

            self.noc_interface.send(receiver_ready_request, None)

        yield 'wait for sender send data '

        # 收到sender 发送的数据，写入到内存中
        local_memory_write_request = BusPayload(
            src='transfer', dst='buffer', data_size=transfer_info.len,
            payload=MemoryRequest(
                access_type='write', addr=transfer_info.dst_addr,
                data_size=transfer_info.len,
            )
        )

        self.transfer_buffer.send(local_memory_write_request, self.finish_execute())

    def noc_receive_handler(self,transfer_info:TransferInfo,bus_payload:BusPayload):
        inter_core_message:InterCoreMessage = bus_payload.payload

        sender_core_id, receiver_core_id = inter_core_message.sender_id, inter_core_message.receiver_id
        assert sender_core_id == transfer_info.imm
        assert receiver_core_id == self.core_id

        if sender_core_id == transfer_info.imm:
            # 正好在等待这个核
            if inter_core_message.status == 'sender_ready':
                # sender后执行,发送receiver就绪
                receiver_ready_request =
            elif inter_core_message.status == 'send_data':
                # 双方都就绪,对面发送数据

        else:
            self.recv_waiting_sender_dict.setdefault(sender_core_id)


    def process_memory(self):
        pass

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

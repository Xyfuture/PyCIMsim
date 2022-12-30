from sim.circuit.module.basic_modules import RegSustain
from sim.circuit.module.registry import registry
from sim.circuit.wire.wire import InWire, UniWire, OutWire, UniPulseWire
from sim.circuit.register.register import RegNext, Trigger
from sim.config.config import CoreConfig
from sim.core.compo.base_core_compo import BaseCoreCompo
from sim.core.compo.connection.payloads import TransferInfo, BusPayload, MemoryRequest, SyncMessage

from sim.core.compo.message_bus import MessageInterface
from sim.network.simple.switch import SwitchInterface


class TransferUnit(BaseCoreCompo):
    def __init__(self, sim, core_id, config: CoreConfig):
        super(TransferUnit, self).__init__(sim)
        self._config = config
        self.core_id = core_id

        self.id_transfer_port = InWire(UniWire, self)

        self._reg_head = RegSustain(sim)
        self._status_input = UniWire(self)
        self._reg_head_output = UniWire(self)
        self._reg_head.connect(self.id_transfer_port, self._status_input, self._reg_head_output)

        self.transfer_buffer = MessageInterface(self, 'transfer')

        self.transfer_busy = OutWire(UniWire, self)

        self.finish_wire = UniPulseWire(self)

        self.func_trigger = Trigger(self)
        self.trigger_input = UniWire(self)
        self.func_trigger.connect(self.trigger_input)

        self.noc_interface = SwitchInterface(self, core_id)

        self._run_state = 'idle'

        self.sync_dict = {}  # 记录一个每个核的sync_cnt
        self.sync_cnt = 1

        self.state_value = 0
        self.wait_core_dict = {}  # core_id:value 等待自己的

        self.wait_core_id = -1  # 等别人的
        self.wait_state = -1

        self.registry_sensitive()

    def initialize(self):
        self._status_input.write(True)

    def calc_compute_latency(self, payload):
        return 10

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
                if data_payload['ex'] == 'transfer':
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
        self.transfer_busy.write(stall_status)

    @registry(['noc_interface'])
    def noc_receive_dispatch(self, bus_payload:BusPayload):
        payload = bus_payload.payload
        if isinstance(payload,SyncMessage):
            if payload.op == 'sync':
                self.sync_receive_handler(bus_payload)
            elif payload.op == 'wait_core':
                self.wait_core_receive_handler(bus_payload)
        else:
            self.memory_receive_handler(bus_payload)
            self.noc_interface.allow_receive()  # 暂时在这里接受

    # local_buffer receive
    @registry(['transfer_buffer'])
    def local_buffer_receive_dispatch(self,bus_payload:BusPayload):
        self.memory_receive_handler(bus_payload)
        self.transfer_buffer.allow_receive() # 暂时在这里接收

    # 发射指令
    @registry(['func_trigger'])
    def process(self):
        reg_head_payload = self._reg_head_output.read()
        data_payload = reg_head_payload['data_payload']

        op = data_payload['op']
        self._run_state = op

        if op == 'sync':
            self.execute_sync(data_payload)
        elif op == 'wait_core':
            self.execute_wait_core(data_payload)
        elif op == 'inc_state':
            self.execute_inc_state(data_payload)
        else:
            self.execute_memory(data_payload)

    def execute_sync(self, payload):
        start_core, end_core = payload['start_core'], payload['end_core']

        # 初始化同步dict  发送自己开始的数据给其他的核
        for i in range(start_core, end_core + 1):
            self.sync_dict[i] = 0

            # start_payload = {'src': self.core_id, 'dst': i, 'data_size': 1,
            #                  'op': 'sync', 'message': 'start', 'sync_cnt': self.sync_cnt}

            start_sync_request = BusPayload(
                src=self.core_id,dst=i,data_size=1,
                payload=SyncMessage(
                    op='sync',message='start',sync_cnt=self.sync_cnt
                )
            )


            self.noc_interface.send(start_sync_request, None)

    # 处理所有与sync有关的信息,不论目前是什么状态
    def sync_receive_handler(self, bus_payload:BusPayload):
        def send_sync_finish_info():

            if len(self.sync_dict):
                k, v = self.sync_dict.popitem()
                # finish_payload = {'src': self.core_id, 'dst': k, 'data_size': 1,
                #                   'op': 'sync', 'message': 'finish', 'sync_cnt': self.sync_cnt - 1}

                finish_sync_request = BusPayload(
                    src=self.core_id,dst=k,data_size=1,
                    payload=SyncMessage(
                        op='sync',message='finish',sync_cnt=self.sync_cnt -1
                    )
                )

                self.noc_interface.send(finish_sync_request, send_sync_finish_info)
            else:
                self.finish_execute()

        if self._run_state == 'sync':
            sync_message:SyncMessage = bus_payload.payload
            if sync_message.message == 'start':
                src = bus_payload.src
                sync_cnt = sync_message.sync_cnt
                if self.sync_cnt == sync_cnt:
                    self.sync_dict[src] = sync_cnt

                for k, v in self.sync_dict.items():
                    if not v:  # 仍有未运行结束的
                        self.noc_interface.allow_receive()
                        return
                # 全部都已经运行到了
                self.sync_cnt += 1
                send_sync_finish_info()
            elif sync_message.message == 'finish':
                if self.sync_cnt == sync_message.sync_cnt:
                    self.sync_dict.clear()
                    self.sync_cnt += 1
                    self.finish_execute()
        else:  # 当前如果不在运行sync指令 就直接跳过
            assert False
        self.noc_interface.allow_receive()

    def execute_wait_core(self, payload:TransferInfo):

        self.wait_state = payload['state']
        self.wait_core_id = payload['core_id']

        # new_payload = {'src': self.core_id, 'dst': self.wait_core_id, 'data_size': 1,
                       # 'op': 'wait_core', 'message': 'start', 'state': self.wait_state}

        start_wait_core_request = BusPayload(
            src=self.core_id,dst=self.wait_core_id,data_size=1,
            payload =SyncMessage(
                op='wait_core',message='start',state=self.wait_state
            )
        )

        self.noc_interface.send(start_wait_core_request, None)

    # 处理所有与wait_core有关的信息,不论目前是什么状态
    def wait_core_receive_handler(self, bus_payload:BusPayload):
        sync_message:SyncMessage = bus_payload.payload
        if sync_message.message == 'start':
            # 其他核开始等待本核
            state = sync_message.state  # 等待本核的state
            if self.state_value >= state:
                # new_payload = {'src': self.core_id, 'dst': bus_payload['src'], 'data_size': 1,
                #                'op': 'wait_core', 'message': 'finish', 'state': self.state_value}
                finish_wait_core_request = BusPayload(
                    src=self.core_id,dst=bus_payload.src,data_size=1,
                    payload=SyncMessage(
                        op='wait_core',message='finish',state=self.state_value
                    )
                )
                self.noc_interface.send(finish_wait_core_request, None)
            else:
                self.wait_core_dict[bus_payload['src']] = state
        elif sync_message.message == 'finish':
            assert self._run_state == 'wait_core'
            assert self.wait_state <= bus_payload['state']

            self.finish_execute()

        self.noc_interface.allow_receive()

    def execute_inc_state(self, payload):
        self.state_value += 1

        finish_list = []
        for k, v in self.wait_core_dict.items():
            if v <= self.state_value:
                finish_list.append(k)
        for k in finish_list:
            # tmp_payload = {'src': self.core_id, 'dst': k, 'data_size': 1,
            #                'op': 'wait_core', 'message': 'finish', 'state': self.state_value}

            finish_wait_core_request = BusPayload(
                src=self.core_id, dst=k, data_size=1,
                payload=SyncMessage(
                    op='wait_core', message='finish', state=self.state_value
                )
            )

            self.noc_interface.send(finish_wait_core_request, None)
            del self.wait_core_dict[k]
        self.make_event(self.finish_execute,self.current_time+1)

    def execute_memory(self, payload: TransferInfo):

        op = payload.op
        if op == 'dram_to_global':
            dram_read_reqeust = BusPayload(
                src=self.core_id, dst='dram', data_size=1,
                payload=MemoryRequest(
                    access_type='read', addr=payload.mem_access_info.src_addr,
                    data_size=payload.mem_access_info.data_size
                )
            )
            self.noc_interface.send(dram_read_reqeust, None)
        elif op in ['global_to_local', 'global_to_dram', 'global_cpy']:
            global_read_reqeust = BusPayload(
                src=self.core_id, dst='global', data_size=1,
                payload=MemoryRequest(
                    access_type='read', addr=payload.mem_access_info.src_addr,
                    data_size=payload.mem_access_info.data_size
                )
            )
            self.noc_interface.send(global_read_reqeust, None)
        elif op in ['local_to_global', 'local_cpy']:
            local_read_request = BusPayload(
                src='transfer', dst='buffer', data_size=1,
                payload=MemoryRequest(
                    access_type='read', addr=payload.mem_access_info.src_addr,
                    data_size=payload.mem_access_info.data_size
                )
            )
            self.transfer_buffer.send(local_read_request, None)
        elif op == 'global_clr':
            global_write_request = BusPayload(
                src=self.core_id, dst='global', data_size=payload.mem_access_info.data_size,
                payload=MemoryRequest(
                    access_type='write', addr=payload.mem_access_info.src_addr,
                    data_size=payload.mem_access_info.data_size
                )
            )
            self.noc_interface.send(global_write_request, self.finish_execute)
        elif op == 'local_clr':
            local_write_request = BusPayload(
                src='transfer', dst='buffer', data_size=payload.mem_access_info.data_size,
                payload=MemoryRequest(
                    access_type='write', addr=payload.mem_access_info.src_addr,
                    data_size=payload.mem_access_info.data_size
                )
            )
            self.transfer_buffer.send(local_write_request, self.finish_execute)

    def memory_receive_handler(self, bus_payload: BusPayload):
        # 第二次执行时的操作,读取的数据到了,转发到第二个
        reg_head_payload = self._reg_head_output.read()
        data_payload: TransferInfo = reg_head_payload['data_payload']

        op = data_payload.op
        if op in ['global_to_local', 'local_cpy']:
            local_write_request = BusPayload(
                src='transfer', dst='buffer', data_size=data_payload.mem_access_info.data_size,
                payload=MemoryRequest(
                    access_type='write', addr=data_payload.mem_access_info.dst_addr,
                    data_size=data_payload.mem_access_info.data_size
                )
            )
            self.transfer_buffer.send(local_write_request, self.finish_execute)
        elif op in ['dram_to_global', 'local_to_global', 'global_cpy']:
            global_write_request = BusPayload(
                src=self.core_id, dst='global', data_size=data_payload.mem_access_info.data_size,
                payload=MemoryRequest(
                    access_type='write', addr=data_payload.mem_access_info.dst_addr,
                    data_size=data_payload.mem_access_info.data_size
                )
            )
            self.noc_interface.send(global_write_request, self.finish_execute)
        elif op == 'global_to_dram':
            dram_write_request = BusPayload(
                src=self.core_id, dst='dram', data_size=data_payload.mem_access_info.data_size,
                payload=MemoryRequest(
                    access_type='write', addr=data_payload.mem_access_info.dst_addr,
                    data_size=data_payload.mem_access_info.data_size
                )
            )
            self.noc_interface.send(dram_write_request, self.finish_execute)
        else:
            assert False





    def finish_execute(self):
        # print("core_id:{} finish sync".format(self.core_id))
        self._run_state = 'idle'
        self.finish_wire.write(True)


    def get_running_status(self):
        print("Transfer> "
              f"pc:{self._reg_head_output.read()['data_payload'].pc}")

# 一些格式信息
# {'src':1,'dst':2,'data_size':1,'op':'sync','message':'start/finish','sync_cnt':sync_cnt}
# {'src':1,'dst':2,'data_size':1,'op':'wait_core','message':'finish','state':self.state_value}
# {'src':1,'dst':2,'data_size':1,'op':'wait_core','message':'start','state':self.wait_state}

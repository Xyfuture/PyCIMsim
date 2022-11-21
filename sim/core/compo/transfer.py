from sim.circuit.module.basic_modules import RegSustain
from sim.circuit.module.registry import registry
from sim.circuit.wire.wire import InWire, UniWire, OutWire, UniPulseWire
from sim.circuit.register.register import RegNext, Trigger
from sim.core.compo.base_core_compo import BaseCoreCompo

from sim.core.compo.message_bus import MessageInterface
from sim.network.simple.switch import SwitchInterface


class TransferUnit(BaseCoreCompo):
    def __init__(self, sim, core_id, config=None):
        super(TransferUnit, self).__init__(sim)
        self._config = config
        self.core_id = core_id

        self.id_transfer_port = InWire(UniWire,self)

        self._reg_head = RegSustain(sim)
        self._status_input = UniWire(self)
        self._reg_head_output = UniWire(self)
        self._reg_head.connect(self.id_transfer_port,self._status_input,self._reg_head_output)

        self.transfer_buffer = MessageInterface(self,'transfer')

        self.transfer_busy = OutWire(UniWire,self)

        self.finish_wire = UniPulseWire(self)

        self.func_trigger = Trigger(self)
        self.trigger_input = UniWire(self)
        self.func_trigger.connect(self.trigger_input)

        self.noc_interface = SwitchInterface(self, core_id)

        self._run_state = 'idle'

        self.sync_dict = {} # 记录一个每个核的sync_cnt
        self.sync_cnt = 1

        self.state_value = 0
        self.wait_core_dict = {} # core_id:value 等待自己的

        self.wait_core_id = -1 # 等别人的
        self.wait_state = -1

        self.registry_sensitive()

    def initialize(self):
        self._status_input.write(True)

    def calc_compute_latency(self,payload):
        return 10

    @registry(['_reg_head_output','finish_wire'])
    def check_stall_status(self):
        reg_head_payload = self._reg_head_output.read()
        finish_info = self.finish_wire.read()

        data_payload,idle = reg_head_payload['data_payload'],reg_head_payload['status']

        new_idle_status = True
        trigger_status = False
        stall_status = {'busy':False}

        if idle:
            if data_payload:
                if data_payload['ex'] == 'transfer':
                    new_idle_status = False
                    trigger_status = True
                    stall_status = {'busy':True}
        else:
            if finish_info:
                new_idle_status = True
                trigger_status = False
                stall_status = {'busy':False}
            else:
                new_idle_status = False
                trigger_status = False
                stall_status = {'busy':True}

        self._status_input.write(new_idle_status)
        self.trigger_input.write(trigger_status)
        self.transfer_busy.write(stall_status)

    @registry(['func_trigger'])
    def process(self):
        reg_head_payload = self._reg_head_output.read()
        data_payload = reg_head_payload['data_payload']

        op = data_payload['aluop']
        self._run_state = op

        if op == 'sync':
            pass
        elif op == 'wait_core':
            pass
        elif op == 'inc_state':
            pass

    # 发射指令
    def execute_sync(self,payload):
        pass

    def execute_wait_core(self,payload):

        self.wait_state = payload['state']
        self.wait_core_id = payload['core_id']

        new_payload = {'src':self.core_id,'dst':self.wait_core_id,'data_size':1,
                       'op':'wait_core','message':'start','state':self.wait_state}

        self.noc_interface.send(new_payload,None)

    def execute_inc_state(self,payload):
        self.state_value += 1

        finish_list = []
        for k,v in self.wait_core_dict.items():
            if v<= self.state_value:
                finish_list.append(k)
        for k in finish_list:
            tmp_payload = {'src':self.core_id,'dst':k,'data_size':1,
                           'op':'wait_core','message':'finish','state':self.state_value}
            self.noc_interface.send(tmp_payload,None)
            del self.wait_core_dict[k]




    @registry(['noc_interface'])
    def noc_receive_dispatch(self,payload):
        op = payload['op']

        if op == 'sync':
            self.sync_receive_handler(payload)
        elif op == 'wait_core':
            self.wait_core_receive_handler(payload)

    # 处理所有与sync有关的信息,不论目前是什么状态
    def sync_receive_handler(self,payload):
        def send_sync_finish_info():
            if len(self.sync_dict):
                k,v = self.sync_dict.popitem()
                finish_payload = {'src':self.core_id,'dst':k,'data_size':1,
                           'op':'sync','message':'finish','sync_cnt':sync_cnt}

                self.noc_interface.send(finish_payload,send_sync_finish_info)
            else:
                self.finish_execute()

        if self._run_state == 'sync':
            if payload['message'] == 'start':
                src = payload['src']
                sync_cnt = payload['sync_cnt']
                self.sync_dict[src] = sync_cnt

                for k,v in self.sync_dict.items():
                    if not v: # 仍有未运行结束的
                        self.noc_interface.allow_receive()
                        return
                # 全部都已经运行到了
                send_sync_finish_info()
            elif payload['message'] == 'finish':
                if self.sync_cnt == payload['sync_cnt']:
                    self.sync_dict.clear()
                    self.finish_execute()
        else: # 当前如果不在运行sync指令 就直接跳过
            pass
        self.noc_interface.allow_receive()

    # 处理所有与wait_core有关的信息,不论目前是什么状态
    def wait_core_receive_handler(self,payload):
        if payload['message'] == 'start':
            # 其他核开始等待本核
            state = payload['state'] # 等待本核的state
            if self.state_value >= state:
                new_payload = {'src':self.core_id,'dst':payload['src'],'data_size':1,
                               'op':'wait_core','message':'finish','state':self.state_value}
                self.noc_interface.send(new_payload,None)
            else:
                self.wait_core_dict[payload['src']] = state
        elif payload['message'] == 'finish':
            assert self._run_state == 'wait_core'
            assert self.wait_state <= payload['state']

            self.finish_execute()
        self.noc_interface.allow_receive()


    def memory_receive_handler(self,payload):
        pass

    def finish_execute(self):
        self._run_state = 'idle'
        self.finish_wire.write(True)





# 一些格式信息
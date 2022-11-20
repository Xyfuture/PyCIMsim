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
        self.sync_dict = {}

        self.state_value = 0

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

        if op == 'sync':
            pass
        elif op == 'wait_core':
            pass
        elif op == 'inc_state':
            pass


    def sync_receive_handler(self,payload):
        pass

    def wait_core_receive_handler(self,payload):
        pass

    # def

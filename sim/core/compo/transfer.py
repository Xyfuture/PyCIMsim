from sim.circuit.module.basic_modules import RegSustain
from sim.circuit.module.registry import registry
from sim.circuit.port.port import UniReadPort, UniWritePort, UniPulseWire
from sim.circuit.register.register import RegNext, Trigger
from sim.core.compo.base_core_compo import BaseCoreCompo

from sim.core.compo.message_bus import MessageInterface
from sim.network.simple.switch import SwitchInterface


class TransferUnit(BaseCoreCompo):
    def __init__(self, sim, core_id, config=None):
        super(TransferUnit, self).__init__(sim)
        self._config = config

        self._reg_head = RegSustain(sim)

        self.id_transfer_port = self._reg_head.get_data_input_read_port()

        self._status_input_write_port = self._reg_head.get_status_input_write_port()
        self._reg_head_output_read_port = self._reg_head.get_output_read_port()

        self.transfer_buffer = MessageInterface(self,'transfer')

        self.transfer_busy = UniWritePort(self)

        self.finish_wire = UniPulseWire(self)

        self.func_trigger = Trigger(self)
        self.trigger_write_port = self.func_trigger.get_input_write_port()

        self._run_state = 'idle'

        self._core_id = core_id
        self.noc_interface = SwitchInterface(self, core_id)

        self.sync_dict = {}

        self.state_value = 0

        self.registry_sensitive()

    def initialize(self):
        self._status_input_write_port.write(True)

    def calc_compute_latency(self):
        return 10

    @registry(['_reg_head_output_read_port','finish_wire'])
    def check_stall_status(self):
        reg_head_payload = self._reg_head_output_read_port.read()
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

        self._status_input_write_port.write(new_idle_status)
        self.trigger_write_port.write(trigger_status)
        self.transfer_busy.write(stall_status)

    @registry(['func_trigger'])
    def process(self):
        decode_payload = self._reg_head_output_read_port.read()

        op = decode_payload['op']
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

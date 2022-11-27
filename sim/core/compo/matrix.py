from sim.circuit.module.basic_modules import RegSustain
from sim.circuit.module.registry import registry
# from sim.circuit.port.port import UniReadPort, UniWritePort, UniPulseWire
from sim.circuit.wire.wire import InWire, UniWire, OutWire, UniPulseWire
from sim.circuit.register.register import RegNext, Trigger
from sim.config.config import CoreConfig
from sim.core.compo.base_core_compo import BaseCoreCompo

from sim.core.compo.message_bus import MessageInterface


class MatrixUnit(BaseCoreCompo):
    def __init__(self,sim,config:CoreConfig=None):
        super(MatrixUnit, self).__init__(sim)
        self._config = config

        self.id_matrix_port = InWire(UniWire,self)

        self._reg_head = RegSustain(sim)
        self._status_input = UniWire(self)
        self._reg_head_output = UniWire(self)
        self._reg_head.connect(self.id_matrix_port,self._status_input,self._reg_head_output)

        self.matrix_buffer = MessageInterface(self,'matrix')

        self.matrix_busy = OutWire(UniWire,self)

        self.finish_wire = UniPulseWire(self)

        self.func_trigger = Trigger(self)
        self.trigger_input = UniPulseWire(self)
        self.func_trigger.connect(self.trigger_input)

        self.registry_sensitive()

    def initialize(self):
        self._status_input.write(True)

    def calc_compute_latency(self,payload):
        if self._config:
            return self._config.matrix_latency
        else:
            return 1000

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
        self.matrix_busy.write(stall_status)

    @registry(['func_trigger'])
    def process(self):
        decode_payload = self._reg_head_output.read()

        if not decode_payload:
            return

        memory_read_request = {'src':'matrix','dst':'buffer','data_size':128,'access_type':'read'}
        self.matrix_buffer.send(memory_read_request,None)

    @registry(['matrix_buffer'])
    def execute_gemv(self,payload):
        latency = self.calc_compute_latency(self._reg_head_output.read()['data_payload'])
        memory_write_request = {'src':'matrix','dst':'buffer','data_size':128,'access_type':'write'}
        f = lambda:self.matrix_buffer.send(memory_write_request,self.finish_execute)

        self.make_event(f,self.current_time+latency)

    def finish_execute(self):
        print("finish gemv time:{}".format(self.current_time))

        self.matrix_buffer.allow_receive()
        self.finish_wire.write(True)



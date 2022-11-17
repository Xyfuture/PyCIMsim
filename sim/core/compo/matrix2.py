from sim.circuit.module.basic_modules import RegSustain
from sim.circuit.module.registry import registry
from sim.circuit.port.port import UniReadPort, UniWritePort, UniPulseWire
from sim.circuit.register.register import RegNext, Trigger
from sim.core.compo.base_core_compo import BaseCoreCompo

from sim.core.compo.message_bus import MessageInterface


class MatrixUnit(BaseCoreCompo):
    def __init__(self,sim,config=None):
        super(MatrixUnit, self).__init__(sim)
        self._config = config

        self._reg_head = RegSustain(sim)

        self.id_matrix_port = self._reg_head.get_data_input_read_port()

        self._status_input_write_port = self._reg_head.get_status_input_write_port()
        self._reg_head_output_read_port = self._reg_head.get_output_read_port()

        self.matrix_buffer = MessageInterface(self,'matrix')

        self.matrix_busy = UniWritePort(self)

        self.finish_wire = UniPulseWire(self)
        self.func_trigger = Trigger(self)
        self.trigger_write_port = self.func_trigger.get_input_write_port()

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
                if data_payload['op'] == 'gemv':
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
        self.matrix_busy.write(stall_status)

    @registry(['func_trigger'])
    def process(self):
        decode_payload = self._reg_head_output_read_port.read()

        if not decode_payload:
            return

        memory_read_request = {'src':'matrix','dst':'buffer','data_size':128,'access_type':'read'}
        self.matrix_buffer.send(memory_read_request,None)

    @registry(['matrix_buffer'])
    def execute_gemv(self,payload):
        latency = self.calc_compute_latency()
        memory_write_request = {'src':'matrix','dst':'buffer','data_size':128,'access_type':'write'}
        f = lambda:self.matrix_buffer.send(memory_write_request,self.finish_execute)

        self.make_event(f,self.current_time+latency)

    def finish_execute(self):
        print("finish gemv time:{}".format(self.current_time))

        self.matrix_buffer.allow_receive()
        self.finish_wire.write(True)



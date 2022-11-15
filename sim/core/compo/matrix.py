from sim.circuit.module.registry import registry
from sim.circuit.port.port import UniReadPort, UniWritePort
from sim.circuit.register.register import RegNext
from sim.core.compo.base_core_compo import BaseCoreCompo
from sim.des.simulator import Simulator
from sim.des.event import Event
from sim.des.base_compo import BaseCompo
from sim.des.stime import Stime

from sim.core.utils.bus.message_bus import MessageInterface

class MatrixUnit(BaseCoreCompo):
    def __init__(self,sim,config=None):
        super(MatrixUnit, self).__init__(sim)
        self._config = config

        self._reg = RegNext(self)
        self._reg_read_port = self._reg.get_output_read_port()
        self._reg_write_port = self._reg.get_input_write_port()

        self.id_matrix_port = UniReadPort(self)

        self.matrix_buffer = MessageInterface(self,"matrix",self.execute_gemv)

        self.matrix_busy = UniWritePort(self)

        # self.request_type_read,self.request_type_write = make_bind_ports(self,self.process)

        self.registry_sensitive()

    def initialize(self):
        pass

    def calc_compute_latency(self):
        return 10

    @registry(['id_matrix_port'])
    def update_reg(self):
        payload = self.id_matrix_port.read()
        if payload:
            self._reg_write_port.write(payload)

    @registry(['_reg_read_port'])
    def process(self):
        self.matrix_busy.write({'busy':True})

        memory_read_request = {'src':'matrix','dst':'buffer','data_size':128,'access_type':'read'}

        self.matrix_buffer.send(memory_read_request,None)

    def execute_gemv(self,payload):
        latency = self.calc_compute_latency()
        memory_write_request = {'src':'matrix','dst':'buffer','data_size':128,'access_type':'write'}
        f = lambda:self.matrix_buffer.send(memory_write_request,self.finish_execute)

        self.make_event(f,self.current_time+latency)

    def finish_execute(self):
        print("finish gemv time:{}".format(self.current_time))
        self.matrix_busy.write({'busy':False})
        self.matrix_buffer.allow_receive()




from __future__ import annotations
import random

from sim.core.compo.base_core_compo import BaseCoreCompo
from sim.core.test_compo.dummy_local_buffer import BufferPacket
from sim.core.utils.port.bi_port import BiPort
from sim.des.simulator import Simulator
from sim.des.event import Event
from sim.des.base_compo import BaseCompo
from sim.des.stime import Stime



class DummyMatrix(BaseCoreCompo):
    def __init__(self,sim):
        super(DummyMatrix, self).__init__(sim)

        self._matrix_port = BiPort(self,self.process_awk)


    def initialize(self):
        self.gen_random_data()


    def process_awk(self):
        payload = self._matrix_port.read(self.current_time)
        print("Matrix get AWK : Payload:{} {}".format(payload,self.current_time))
        self.gen_random_data()


    def gen_random_data(self):
        latency = random.randint(1,100)
        payload = random.randint(10,20)
        print("Matrix send : Payload:{} {}".format(payload, self.current_time+latency))

        self._matrix_port.write(BufferPacket(payload),self.current_time+latency)

class DummyVector(BaseCoreCompo):
    def __init__(self, sim):
        super(DummyVector, self).__init__(sim)

        self._vector_port = BiPort(self, self.process_awk)

    def initialize(self):
        self.gen_random_data()

    def process_awk(self):
        payload = self._vector_port.read(self.current_time)
        print("Vector get AWK : Payload:{} {}".format(payload, self.current_time))
        self.gen_random_data()

    def gen_random_data(self):
        latency = random.randint(1, 100)
        payload = random.randint(10, 20)
        print("Vector send : Payload:{} {}".format(payload, self.current_time + latency))

        self._vector_port.write(BufferPacket(payload), self.current_time + latency)


class DummyTransfer(BaseCoreCompo):
    def __init__(self, sim):
        super(DummyTransfer, self).__init__(sim)

        self._transfer_port = BiPort(self, self.process_awk)

    def initialize(self):
        self.gen_random_data()

    def process_awk(self):
        payload = self._transfer_port.read(self.current_time)
        print("Transfer get AWK : Payload:{} {}".format(payload, self.current_time))
        self.gen_random_data()

    def gen_random_data(self):
        latency = random.randint(1, 100)
        payload = random.randint(10, 20)
        print("Transfer send : Payload:{} {}".format(payload, self.current_time + latency))

        self._transfer_port.write(BufferPacket(payload), self.current_time + latency)
import copy

from sim.core.compo.base_core_compo import BaseCoreCompo
from sim.des.simulator import Simulator
from sim.des.event import Event
from sim.des.base_compo import BaseCompo
from sim.des.stime import Stime
from sim.core.utils.port.uni_port import UniReadPort, UniWritePort
from sim.core.utils.register.register import RegEnable, RegNext

from sim.des.utils import fl


class RegisterFiles(BaseCoreCompo):
    def __init__(self, sim):
        super(RegisterFiles, self).__init__(sim)

        self.reg_file_read_addr = UniReadPort(self, self.read_value)
        self.reg_file_read_data = UniWritePort(self)

        self.reg_file_write = UniReadPort(self, fl(self.read_value, self.update_value))

        self._reg_files = RegNext(self, self.read_value)

    def initialize(self):
        tmp = [0 for _ in range(32)]
        self._reg_files.initialize(tmp)

    # def process(self):
    #     self.read_value()
    #     self.update_value()

    def read_value(self):

        scalar_payload = self.reg_file_write.read(self.current_time)
        decode_payload = self.reg_file_read_addr.read(self.current_time)
        current_reg_files = self._reg_files.read()

        if decode_payload:
            rs1_addr, rs2_addr = decode_payload['rs1_addr'], decode_payload['rs2_addr']
            value = {'rs1_data': current_reg_files[rs1_addr], 'rs2_data': current_reg_files[rs2_addr]}

            if scalar_payload:
                rd_addr, rd_data = scalar_payload['rd_addr'], scalar_payload['rd_data']
                if rs1_addr == rd_addr:
                    value['rs1_data'] = rd_data
                if rs2_addr == rd_addr:
                    value['rs2_data'] = rd_data

            self.reg_file_read_data.write(value)

    def update_value(self):
        scalar_payload = self.reg_file_write.read(self.current_time)

        if scalar_payload:
            rd_addr, rd_data = scalar_payload['rd_addr'], scalar_payload['rd_data']
            current_reg_files = copy.deepcopy(self._reg_files.read())

            # TODO 让一些dict仅可读,并方便复制
            current_reg_files[rd_addr] = rd_data
            self._reg_files.write(current_reg_files)

            print("register #{} value:{}".format(3,current_reg_files[3]))
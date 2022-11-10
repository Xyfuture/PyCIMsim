import copy

from sim.core.compo.base_core_compo import BaseCoreCompo
from sim.des.simulator import Simulator
from sim.des.event import Event
from sim.des.base_compo import BaseCompo
from sim.des.stime import Stime
from sim.core.utils.port.uni_port import UniReadPort, UniWritePort
from sim.core.utils.register.register import RegEnable, RegNext


class RegisterFiles(BaseCoreCompo):
    def __init__(self, sim):
        super(RegisterFiles, self).__init__(sim)

        self.reg_file_read_addr = UniReadPort(self, self.process)
        self.reg_file_read_data = UniWritePort(self)

        self.reg_file_write = UniReadPort(self, self.process)

        self._reg_files = RegNext(self, self.process)

    def initialize(self):
        pass

    def process(self):
        scalar_payload = self.reg_file_write.read(self.current_time)
        decode_payload = self.reg_file_read_addr.read(self.current_time)

        if scalar_payload:
            self.update_value(scalar_payload)

        if decode_payload:
            value = self.read_value(decode_payload)
            if scalar_payload:
                bypass_value = self.bypass(scalar_payload,decode_payload)
                for k in bypass_value:
                    value[k] = bypass_value[k]
            # 写回去
            self.reg_file_read_data.write(value, self.next_update_epsilon)


    def read_value(self, decode_payload):
        if decode_payload:
            rs1_addr, rs2_addr = decode_payload['rs1_addr'], decode_payload['rs2_addr']
            current_reg_files = self._reg_files.read()
            value = {'rs1_data': current_reg_files[rs1_addr], 'rs2_data': current_reg_files[rs2_addr]}

            return value
        return None

    def bypass(self, scalar_payload, decode_payload):
        if scalar_payload and decode_payload:
            rd_addr, rd_data = scalar_payload['rd_addr'], scalar_payload['rd_data']
            rs1_addr, rs2_addr = decode_payload['rs1_addr'], decode_payload['rs2_addr']
            bypass_value = {}
            if rs1_addr == rd_addr:
                bypass_value['rs1_data'] = rd_data
            if rs2_addr == rd_addr:
                bypass_value['rs2_data'] = rd_data
            return bypass_value
        return {}

    def update_value(self, scalar_payload):
        if scalar_payload:
            rd_addr, rd_data = scalar_payload['rd_addr'], scalar_payload['rd_data']
            current_reg_files = copy.deepcopy(self._reg_files.read())

            # TODO 让一些dict仅可读,并方便复制
            current_reg_files[rd_addr] = rd_data
            self._reg_files.write(current_reg_files)

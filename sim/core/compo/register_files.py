import copy

from sim.circuit.module.registry import registry
from sim.circuit.wire.wire import InWire, UniWire, OutWire

from sim.circuit.register.register import RegNext
from sim.config.config import CoreConfig
from sim.core.compo.base_core_compo import BaseCoreCompo
from sim.core.compo.connection.payloads import RegFileReadRequest


class RegisterFiles(BaseCoreCompo):
    def __init__(self, sim, compo, config: CoreConfig):
        super(RegisterFiles, self).__init__(sim, compo)
        self._config = config

        self.reg_file_read_addr = InWire(UniWire, sim, self)
        self.reg_file_read_data = OutWire(UniWire, sim, self)

        self.reg_file_write = InWire(UniWire, sim, self)

        self._reg_files = RegNext(sim, self)

        self._reg_files_output = UniWire(sim, self)
        self._reg_files_input = UniWire(sim, self)

        self._reg_files.connect(self._reg_files_input, self._reg_files_output)

        self.registry_sensitive()

    def initialize(self):
        tmp = [0 for _ in range(32)]
        self._reg_files.init(tmp)

    @registry(['_reg_files_output', 'reg_file_read_addr', 'reg_file_write'])
    def read_value(self):
        scalar_payload = self.reg_file_write.read()
        decode_payload: RegFileReadRequest = self.reg_file_read_addr.read()
        current_reg_files = self._reg_files_output.read()

        if decode_payload:
            rd_addr, rs1_addr, rs2_addr = decode_payload['rd_addr'], \
                decode_payload['rs1_addr'], \
                decode_payload['rs2_addr']

            value = {'rd_data': current_reg_files[rd_addr],
                     'rs1_data': current_reg_files[rs1_addr],
                     'rs2_data': current_reg_files[rs2_addr]}

            if scalar_payload:
                new_rd_addr, new_rd_data = scalar_payload['rd_addr'], scalar_payload['rd_data']
                if rd_addr == new_rd_addr:
                    value['rd_data'] = new_rd_data
                if rs1_addr == new_rd_addr:
                    value['rs1_data'] = new_rd_data
                if rs2_addr == rd_addr:
                    value['rs2_data'] = new_rd_data

            self.reg_file_read_data.write(value)

    @registry(['reg_file_write'])
    def update_value(self):
        # 这里的实现需要特别注意,因为有点破坏规则
        scalar_payload = self.reg_file_write.read()

        if scalar_payload:
            rd_addr, rd_data = scalar_payload['rd_addr'], scalar_payload['rd_data']
            current_reg_files = copy.deepcopy(self._reg_files_output.read())  # 这里稍微有点破坏规则,但是为了省事,还是简化吧

            current_reg_files[rd_addr] = rd_data
            self._reg_files_input.write(current_reg_files)

            # print("register #{} value:{}".format(3,current_reg_files[3]))

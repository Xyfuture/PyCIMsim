from sim.config.config import CoreConfig
from sim.core.compo.local_buffer import LocalBuffer
from sim.core.compo.matrix import MatrixUnit
from sim.core.compo.message_bus import MessageBus
from sim.core.compo.vector import VectorUnit
from sim.core.inst.loader import load_dict
from sim.des.simulator import Simulator

from sim.core.compo.inst_fetch import InstFetch
from sim.core.compo.inst_decode import InstDecode, DecodeForward
from sim.core.compo.register_files import RegisterFiles
from sim.core.compo.scalar import ScalarUnit
from sim.core.compo.controller import Controller

# inst_buffer = [
#     {'op': 'addi', 'rd_addr': 1, 'rs1_addr': 0, 'imm': 100},
#     {'op': 'addi', 'rd_addr': 2, 'rs1_addr': 0, 'imm': 100},
#     {'op': 'gemv'},
#     {'op': 'add', 'rd_addr': 3, 'rs1_addr': 3, 'rs2_addr': 2},
#     {'op': 'j', 'offset': -3},
#     {'op': 'add', 'rd_addr': 3, 'rs1_addr': 1, 'rs2_addr': 2}
# ]

file_path = r'D:\code\test\core1.txt'
inst_buffer = load_dict(file_path)

if __name__ == "__main__":
    sim = Simulator()
    core_config = CoreConfig()

    inst_fetch = InstFetch(sim, None, core_config)
    inst_decode = InstDecode(sim, None, core_config)
    forward = DecodeForward(sim, None)
    ctrl = Controller(sim, None)
    scalar = ScalarUnit(sim, None, core_config)
    reg_file = RegisterFiles(sim, None, core_config)

    matrix = MatrixUnit(sim, None, core_config)
    vector = VectorUnit(sim,None,core_config)

    bus = MessageBus(sim, None, core_config.local_bus)
    buffer = LocalBuffer(sim, None, core_config.local_buffer)

    inst_fetch.set_inst_buffer(inst_buffer)

    inst_fetch // inst_decode

    inst_decode // forward
    inst_decode // matrix
    inst_decode // vector
    inst_decode // reg_file
    scalar // reg_file

    inst_decode // ctrl
    inst_fetch // ctrl

    forward // matrix
    forward // scalar
    forward // vector
    #
    bus % matrix.matrix_buffer
    bus % buffer.buffer_port
    bus % vector.vector_buffer

    sim.initialize()
    # sim.run()
    sim.new_run()
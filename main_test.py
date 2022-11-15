from sim.core.compo.local_buffer import LocalBuffer
from sim.core.compo.matrix import MatrixUnit
from sim.core.test_compo.inst_fetch import InstFetch
from sim.core.test_compo.inst_decode import InstDecode
from sim.core.utils.bus.message_bus import MessageBus
from sim.des.simulator import Simulator
from sim.core.utils.port.uni_port import connect_uni_port

from sim.core.compo.inst_fetch import InstFetch
from sim.core.compo.inst_decode import InstDecode
from sim.core.compo.register_files import RegisterFiles
from sim.core.compo.scalar import Scalar
from sim.core.compo.controller import Controller

inst_buffer = [
    {'op': 'addi', 'rd_addr': 1, 'rs1_addr': 0, 'imm': 100},
    {'op':'gemv'},
    {'op': 'addi', 'rd_addr': 2, 'rs1_addr': 0, 'imm': 100},
    {'op': 'add', 'rd_addr': 3, 'rs1_addr': 3, 'rs2_addr': 2},
    {'op':'j','imm':-2},
    {'op': 'add', 'rd_addr': 3, 'rs1_addr': 1, 'rs2_addr': 2}

]

if __name__ == "__main__":
    sim = Simulator()
    inst_fetch = InstFetch(sim)
    inst_decode = InstDecode(sim)
    ctrl = Controller(sim)
    scalar = Scalar(sim)
    reg_file = RegisterFiles(sim)

    matrix = MatrixUnit(sim)
    bus = MessageBus(sim)
    buffer = LocalBuffer(sim)


    inst_fetch.set_inst_buffer(inst_buffer)

    inst_fetch // inst_decode

    inst_decode // scalar

    inst_decode // reg_file
    scalar // reg_file

    inst_decode // ctrl
    inst_fetch // ctrl

    inst_decode // matrix
    #
    bus % matrix.matrix_buffer
    bus % buffer.buffer_port



    sim.initialize()
    sim.run()

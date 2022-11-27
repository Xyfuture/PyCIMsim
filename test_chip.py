from sim.core.core import Core
from sim.des.simulator import Simulator
from sim.network.simple.switch import Network

# core_1_inst = [
#     {'op': 'addi', 'rd_addr': 1, 'rs1_addr': 0, 'imm': 100},
#     {'op': 'addi', 'rd_addr': 2, 'rs1_addr': 0, 'imm': 100},
#     {'op': 'gemv'},
#     {'op': 'sync', 'start_core': 1, 'end_core': 3},
#     {'op': 'j', 'offset': -3},
#     {'op': 'add', 'rd_addr': 3, 'rs1_addr': 1, 'rs2_addr': 2}
#
# ]
#
# core_2_inst = [
#     {'op': 'addi', 'rd_addr': 1, 'rs1_addr': 0, 'imm': 100},
#     {'op': 'addi', 'rd_addr': 2, 'rs1_addr': 0, 'imm': 100},
#     {'op': 'gemv'},
#     {'op': 'sync', 'start_core': 1, 'end_core': 3},
#     {'op': 'j', 'offset': -3},
#     {'op': 'add', 'rd_addr': 3, 'rs1_addr': 1, 'rs2_addr': 2}
#
# ]
#
# core_3_inst = [
#     {'op': 'addi', 'rd_addr': 1, 'rs1_addr': 0, 'imm': 100},
#     {'op': 'addi', 'rd_addr': 2, 'rs1_addr': 0, 'imm': 100},
#     {'op': 'gemv'},
#     {'op': 'sync', 'start_core': 1, 'end_core': 3},
#     {'op': 'j', 'offset': -3},
#     {'op': 'add', 'rd_addr': 3, 'rs1_addr': 1, 'rs2_addr': 2}
#
# ]


core_1_inst = [
    {'op': 'addi', 'rd_addr': 1, 'rs1_addr': 0, 'imm': 100},
    {'op': 'addi', 'rd_addr': 2, 'rs1_addr': 0, 'imm': 100},
    {'op': 'wait_core', 'state': 1, 'core_id': 2},
    {'op': 'gemv','pe_assign':(1,2),'relu':1},
    # {'op': 'j', 'offset': -3},
    {'op': 'add', 'rd_addr': 3, 'rs1_addr': 1, 'rs2_addr': 2}

]

core_2_inst = [
    {'op': 'addi', 'rd_addr': 1, 'rs1_addr': 0, 'imm': 100},
    {'op': 'addi', 'rd_addr': 2, 'rs1_addr': 0, 'imm': 100},
    {'op': 'gemv','pe_assign':(1,2),'relu':1},
    {'op': 'inc_state'},
    # {'op': 'j', 'offset': -3},
    {'op': 'add', 'rd_addr': 3, 'rs1_addr': 1, 'rs2_addr': 2}

]



if __name__ == "__main__":
    sim = Simulator()

    network = Network(sim)

    core_1 = Core(sim, core_1_inst, 1, network)
    core_2 = Core(sim,core_2_inst,2,network)
    # core_3 = Core(sim,core_3_inst,3,network)

    sim.initialize()
    sim.run()

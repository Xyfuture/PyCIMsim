
from sim.core.test_compo.controller import Controller
from sim.core.test_compo.inst_fetch import InstFetch
from sim.core.test_compo.inst_decode import InstDecode
from sim.des.simulator import Simulator

from sim.core.utils.port.uni_port import connect_uni_port


if __name__ == "__main__":
    sim = Simulator()
    inst_fetch = InstFetch(sim)
    inst_decode = InstDecode(sim)
    ctrl = Controller(sim)

    # connect_uni_port(inst_fetch.if_id_port,inst_decode.if_id_port)
    inst_decode // inst_fetch

    inst_fetch // ctrl

    inst_decode // ctrl


    # connect_uni_port(inst_fetch.if_stall, ctrl.if_stall)
    # connect_uni_port(inst_fetch.if_enable, ctrl.if_enable)

    # connect_uni_port(inst_decode.id_stall, ctrl.id_stall)
    # connect_uni_port(inst_decode.id_enable, ctrl.id_enable)

    sim.initialize()

    sim.run()
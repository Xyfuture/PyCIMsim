
from sim.core.test_compo.controller import Controller
from sim.core.test_compo.dummy_local_buffer import DummyLocalBuffer
from sim.core.test_compo.dummy_test_buffer import DummyMatrix, DummyVector, DummyTransfer
from sim.core.test_compo.inst_fetch import InstFetch
from sim.core.test_compo.inst_decode import InstDecode
from sim.des.simulator import Simulator

from sim.core.utils.port.uni_port import connect_uni_port


if __name__ == "__main__":
    sim = Simulator()
    # inst_fetch = InstFetch(sim)
    # inst_decode = InstDecode(sim)
    # ctrl = Controller(sim)
    #
    # inst_decode // inst_fetch
    #
    # inst_fetch // ctrl
    #
    # inst_decode // ctrl



    local_buffer = DummyLocalBuffer(sim)
    matrix = DummyMatrix(sim)
    vector = DummyVector(sim)
    transfer = DummyTransfer(sim)

    local_buffer // matrix
    local_buffer // vector
    local_buffer // transfer


    sim.initialize()

    sim.run()
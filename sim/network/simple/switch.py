from sim.config.config import BusConfig
from sim.core.compo.message_bus import MessageInterface, MessageBus
from sim.des.utils import fl


class SwitchInterface(MessageInterface):
    def __init__(self, compo, interface_id):
        super(SwitchInterface, self).__init__(compo, interface_id)

    def set_receive_callback(self, *callback):
        self._receive_callback = fl(*callback)


class Network(MessageBus):
    def __init__(self, sim, config: BusConfig = None):
        super(Network, self).__init__(sim, config)

    # def calc_transfer_latency(self, bus_payload):
    #     src = bus_payload['src']
    #     dst = bus_payload['dst']
    #     data_size = bus_payload['data_size']
    #
    #
    #     return 10

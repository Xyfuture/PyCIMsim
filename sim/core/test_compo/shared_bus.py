from __future__ import annotations

from sim.core.utils.port.uni_port import UniWritePort, UniReadPort
from sim.des.base_compo import BaseCompo
from sim.des.base_element import BaseElement
from sim.core.utils.port.bi_port import BiPort
from sim.des.event import Event
from sim.des.stime import Stime

# 先不用了


class BusPacket:
    def __init__(self, payload, dst, valid=True, src=0):
        self.src = src
        self.dst = dst

        self.valid = valid
        self.payload = payload


# 需要两条线,一条是数据总线,发送数据和地址信息
# 另一条是传输结束的控制线,表示传输结束,上一次发送已经完毕
class SharedBus(BaseCompo):
    def __init__(self, sim, num):
        super(SharedBus, self).__init__(sim)

        self._node_cnt = num

        self._busy: bool = False

        # 是否需要传输
        self._node_status = [False for _ in range(num)]
        # 传输数据的端口号
        self._node_data_ports = [BiPort(self, self.transfer_payload) for _ in range(num)]

        # 传输结束的ack 确认
        self._node_ack_ports = [UniWritePort(self) for _ in range(num)]

    def initialize(self):
        pass

    def setup_transfer(self, node_id):
        self._node_status[node_id] = self._node_data_ports[node_id].read(self.current_time).valid
        self.transfer_payload()

    def transfer_payload(self):
        if not self._busy:
            for node_id in range(self._node_cnt):
                if self._node_status[node_id]:
                    self._busy = True
                    latency = self.get_transfer_latency()

                    # 注意在延迟期间,可能出现优先级更高的发送了请求,但是,我们仍旧响应当前的
                    f = lambda: {self.finish_transfer(node_id)}

                    time = Stime(self.current_time.tick + latency)
                    self.add_event(Event(self, f, time))

    def get_transfer_latency(self):
        return 10

    def finish_transfer(self, node_id):
        self._busy = False
        self._node_status[node_id] = False

        packet: BusPacket = self._node_data_ports[node_id].read(self.current_time)

        src = node_id
        dst = packet.dst
        payload = packet.payload

        self._node_data_ports[dst].write(BusPacket(payload, dst, True, src), self.next_update_epsilon)
        self._node_ack_ports[src].write(True, self.next_update_epsilon)

        self.transfer_payload()  # 看看有没有还有没有等待传输的

    def __floordiv__(self, other):
        pass

    def connect_data_ports(self, ports):
        assert len(ports) == self._node_cnt
        for i, port in enumerate(ports):
            assert isinstance(port, BiPort)
            self._node_data_ports[i] // port

    def connect_ack_ports(self, ports):
        assert len(ports) == self._node_cnt
        for i, port in enumerate(ports):
            assert isinstance(port, UniReadPort)
            self._node_ack_ports[i] // port

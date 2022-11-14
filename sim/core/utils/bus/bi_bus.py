from __future__ import annotations

import queue
from typing import Dict

from sim.core.compo.base_core_compo import BaseCoreCompo
from sim.core.utils.register.register import RegNext, RegOnce
from sim.des.base_element import BaseElement
from sim.des.stime import Stime


class SharedBus(BaseCoreCompo):
    def __init__(self, sim, config=None):
        super(SharedBus, self).__init__(sim)

        self._config = None

        self._ports: Dict[str, SharedBusPort] = {}
        self._pend_buffer: Dict[str, queue.Queue] = {}  # 先留存这个功能,因为write_ready 没使用

    def writer_create_request(self, port_id):
        payload = self._ports[port_id].output_buffer.read()
        dst = payload['dst']
        self._pend_buffer[dst].put(payload)

        self.reader_issue_request(dst)

    def reader_issue_request(self, port_id):
        if self._ports[port_id].read_ready.read():
            if not self._pend_buffer[port_id].empty():
                payload = self._pend_buffer[port_id].get()
                size = payload['data_size']

                latency = self.calc_transfer_latency(size)
                self.make_event(lambda: self.transfer(payload), self.current_time + latency)

    def transfer(self, payload):
        dst, src = payload['dst'], payload['src']

        self._ports[dst].input_buffer.write(payload)
        self._ports[dst].read_ready.write(False)

        self._ports[src].write_finish_callback()
        # self._ports[src].write_finish.write(True)

    def calc_transfer_latency(self, data_size):
        return 10

    def __mod__(self, port):
        port_id = port.interface_id

        self._ports[port_id] = port
        self._pend_buffer[port_id] = queue.Queue()

        port.read_ready.set_callback(lambda: self.reader_issue_request(port_id))
        port.output_buffer.set_callback(lambda: self.writer_create_request(port_id))

        port.set_bus(self)


class SharedBusPort(BaseElement):
    def __init__(self, compo, port_id: str, read_callback, write_finish_callback):
        super().__init__(compo)

        self._bus: SharedBus = None

        self._port_id = port_id

        self._read_callback = read_callback
        self._write_finish_callback = write_finish_callback

        self.input_buffer = RegNext(compo, self._read_callback)
        self.output_buffer = RegNext(compo, None)

        self.read_ready = RegNext(compo, None)
        self.write_ready = RegNext(compo, None)  # 这个暂时有点问题
        # 暂时先不启用这个功能吧,各个compo必须保证不能连着写,必须前一个结束才能写下一个

        self.write_finish = RegOnce(compo, write_finish_callback)
        # 可能有点争议,暂时启用吧

    def read(self):
        # 不设置 time了,因为没有 None 对应默认情况出现了
        return self.input_buffer.read()

    def write(self, payload):
        assert 'dst' in payload and 'data_size' in payload and 'payload' in payload
        payload['src'] = self._port_id
        self.output_buffer.write(payload)

    def write_finish_callback(self):
        if callable(self._write_finish_callback):
            self._write_finish_callback()

    def finish_read(self):
        self.read_ready.write(True)
        self.input_buffer.write(None)

    def set_read_ready(self, status: bool):
        self.read_ready.write(status)

    def set_bus(self, bus):
        self._bus = bus

    @property
    def port_id(self):
        return self._port_id

    def __mod__(self, other):
        if isinstance(other, SharedBus):
            other.__mod__(self)
        raise "Error class type"

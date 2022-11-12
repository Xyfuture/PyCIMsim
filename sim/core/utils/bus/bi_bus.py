from __future__ import annotations

import queue
from typing import Dict

from sim.core.compo.base_core_compo import BaseCoreCompo
from sim.core.utils.register.register import RegNext
from sim.des.base_element import BaseElement
from sim.des.stime import Stime


class SharedBus(BaseCoreCompo):
    def __init__(self, sim, config=None):
        super(SharedBus, self).__init__(sim)

        self._config = None

        self._ports: Dict[str, SharedBusPort] = {}
        self._current_value = {}
        self._update_time = {}
        self._status = {}  # True for idle , False for busy
        self._buffer_queue: Dict[str, queue.Queue] = {}

    def reader_read_value(self, port_id):
        return self._current_value[port_id]

    def writer_create_request(self, payload):
        dst = payload['dst']
        self._buffer_queue[dst].put(payload)
        self.reader_issue_request(dst)

    def reader_issue_request(self, port_id):
        if self._status[port_id].read():
            if not self._buffer_queue[port_id].empty():
                payload = self._buffer_queue[port_id].get()
                size = payload['data_size']

                latency = self.calc_transfer_latency(size)
                self.make_event(lambda: self.update_value(payload), self.current_time + latency)

    def update_value(self, payload):
        dst, src = payload['dst'], payload['src']
        self._current_value[dst] = payload
        self._update_time[[dst]] = self.current_time

        self._ports[dst].read_callback()
        self._ports[src].write_finish_callback()

    def calc_transfer_latency(self, data_size):
        return 10

    def reader_change_status(self, port_id, status):
        self._status[port_id].write(status)

    def __mod__(self, port):
        port_id = port.port_id

        self._ports[port_id] = port
        self._status[port_id] = RegNext(self, lambda: self.reader_issue_request(port_id))
        self._buffer_queue[port_id] = queue.Queue()
        self._update_time[port_id] = Stime(0, 0)
        self._current_value[port_id] = None

        port.set_bus(self)


class SharedBusPort(BaseElement):
    def __init__(self, compo, port_id:str, read_callback, write_finish_callback):
        super().__init__(compo)

        self._bus: SharedBus = None

        self._port_id = port_id

        self.read_callback = read_callback
        self.write_finish_callback = write_finish_callback

    def read(self):
        # 不设置 time了,因为没有 None 对应默认情况出现了
        return self._bus.reader_read_value(self._port_id)

    def write(self, payload):
        assert 'dst' in payload and 'data_size' in payload and 'payload' in payload
        payload['src'] = self._port_id
        self._bus.writer_create_request(payload)

    def allow_read_next(self, status: bool):
        self._bus.reader_change_status(self._port_id, status)

    def read_callback(self):
        if callable(self.read_callback):
            self.read_callback()

    def write_finish_callback(self):
        if callable(self.write_finish_callback):
            self.write_finish_callback()

    def set_bus(self, bus):
        self._bus = bus

    @property
    def port_id(self):
        return self._port_id

    def __mod__(self, other):
        if isinstance(other,SharedBus):
            other.__mod__(self)
        raise "Error class type"


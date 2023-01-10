from __future__ import annotations

import queue
from math import ceil
from typing import Dict

from sim.config.config import BusConfig
from sim.core.compo.base_core_compo import BaseCoreCompo
from sim.core.compo.connection.payloads import BusPayload
from sim.des.base_compo import BaseCompo
from sim.des.utils import fl


class MessageBus(BaseCoreCompo):
    def __init__(self, sim, compo, config: BusConfig):
        super(MessageBus, self).__init__(sim, compo)

        self._config = config

        self._interfaces: Dict[str, MessageInterface] = {}
        self._pend_buffer: Dict[str, queue.Queue] = {}

    def initialize(self):
        pass

    def sender_create_request(self, payload):
        dst, src = payload['dst'], payload['src']
        self._pend_buffer[dst].put(payload)
        self.receiver_issue_request(dst)

    def receiver_issue_request(self, interface_id):
        if self._interfaces[interface_id].receive_ready:
            if not self._pend_buffer[interface_id].empty():
                payload = self._pend_buffer[interface_id].get()

                # size = payload['data_size']
                latency = self.calc_transfer_latency(payload)

                self._interfaces[interface_id].forbid_receive()
                self.make_event(lambda: self.transfer(payload), self.current_time + latency)

    def transfer(self, payload):
        dst, src = payload['dst'], payload['src']

        self._interfaces[dst].receive(payload)
        self._interfaces[src].finish_send()

    def calc_transfer_latency(self, bus_payload: BusPayload):
        data_size = bus_payload['data_size']

        times = ceil(data_size / self._config.bus_width)

        if self._config:
            if self._config.bus_topology == 'shared':
                self.add_dynamic_energy(self._config.energy * times)
                return self._config.latency * times
            elif self._config.bus_topology == 'mesh':
                # memory的补丁
                if isinstance(bus_payload.src, str) or isinstance(bus_payload.dst, str):
                    return self._config.latency * times * 10

                src = (bus_payload.src / self._config.layout[1], bus_payload.src % self._config.layout[1])
                dst = (bus_payload.dst / self._config.layout[1], bus_payload.dst % self._config.layout[1])

                hops = abs(src[0] - dst[0]) + abs(src[1] - dst[1])
                self.add_dynamic_energy(self._config.energy * times * hops)
                return self._config.latency * times * hops
        else:
            return 10

    def __mod__(self, interface):
        interface_id = interface.interface_id

        self._interfaces[interface_id] = interface
        self._pend_buffer[interface_id] = queue.Queue()

        interface.set_bus(self)


class MessageInterface(BaseCompo):
    def __init__(self, sim, compo, interface_id, callback=None):
        super().__init__(sim, compo)

        self._interface_id = interface_id

        self._bus: MessageBus = None
        self._receive_ready = True

        self._receive_callback = fl()
        if callback:
            if isinstance(callback, list):
                for f in callback:
                    self.add_callback(f)
            else:
                self.add_callback(callback)

        self._finish_send_callback_queue = queue.Queue()
        self._send_payload_queue = queue.Queue()
        self._send_ready = True

    def receive(self, payload):
        # self.make_event(lambda : self._process_receive(payload),self.next_handle_epsilon)
        # self._process_receive(payload)
        if callable(self._receive_callback):
            self._receive_callback(payload)

    # def _process_receive(self, payload):
    #     self._receive_ready = False
    #     self._receive_callback(payload)

    def send(self, payload, callback):
        # assert 'dst' in payload and 'data_size' in payload
        payload['src'] = self._interface_id

        self._send_payload_queue.put(payload)
        self._finish_send_callback_queue.put(callback)

        self.try_send()

    def try_send(self):
        if self._send_ready:
            if not self._send_payload_queue.empty():
                payload = self._send_payload_queue.get()
                self._send_ready = False
                self._bus.sender_create_request(payload)

    def forbid_receive(self):
        self._receive_ready = False

    def allow_receive(self):
        self.make_event(self._allow_receive, self.current_time + 1)

    def _allow_receive(self):
        if not self._receive_ready:
            self._receive_ready = True
            self._bus.receiver_issue_request(self._interface_id)

    def finish_send(self):
        self._send_ready = True

        callback = self._finish_send_callback_queue.get()
        if callable(callback):
            callback()

        self.try_send()

    def set_bus(self, bus):
        self._bus = bus

    @property
    def interface_id(self):
        return self._interface_id

    @property
    def receive_ready(self):
        return self._receive_ready

    def __mod__(self, other):
        if isinstance(other, MessageBus):
            other.__mod__(self)
        else:
            raise "Error Operator"

    def add_callback(self, func):
        self._receive_callback.add_func(func)

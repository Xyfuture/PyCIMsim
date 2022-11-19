from __future__ import annotations

import queue
from typing import Dict

from sim.core.compo.base_core_compo import BaseCoreCompo
from sim.des.base_element import BaseElement
from sim.des.stime import Stime
from sim.des.utils import fl


class MessageBus(BaseCoreCompo):
    def __init__(self, sim, config=None):
        super(MessageBus, self).__init__(sim)

        self._config = None

        self._interfaces: Dict[str, MessageInterface] = {}
        self._pend_buffer: Dict[str, queue.Queue] = {}

    def initialize(self):
        pass

    def sender_create_request(self, payload):
        dst, src = payload['dst'], payload['src']
        self._pend_buffer[dst].put(payload)
        self.recevier_issue_request(dst)

    def recevier_issue_request(self, interface_id):
        if self._interfaces[interface_id].receive_ready:
            if not self._pend_buffer[interface_id].empty():
                payload = self._pend_buffer[interface_id].get()

                # size = payload['data_size']
                latency = self.calc_transfer_latency(payload)

                self._interfaces[interface_id].forbid_receive()
                self.make_event(lambda : self.transfer(payload), self.current_time + latency)

    def transfer(self, payload):
        dst, src = payload['dst'], payload['src']

        self._interfaces[dst].receive(payload)
        self._interfaces[src].finish_send()

    def calc_transfer_latency(self, payload):
        return 10

    def __mod__(self, interface):
        interface_id = interface.interface_id

        self._interfaces[interface_id] = interface
        self._pend_buffer[interface_id] = queue.Queue()

        interface.set_bus(self)


class MessageInterface(BaseElement):
    def __init__(self, compo, interface_id,callback=None):
        super().__init__(compo)

        self._interface_id = interface_id

        self._bus: MessageBus = None
        self._receive_ready = True

        self._receive_callback = fl()
        if callback:
            if isinstance(callback,list):
                for f in callback:
                    self.add_callback(f)
            else:
                self.add_callback(callback)

        self._finish_send_callback = None

    def receive(self, payload):
        # self.make_event(lambda : self._process_receive(payload),self.next_handle_epsilon)
        # self._process_receive(payload)
        if callable(self._receive_callback):
            self._receive_callback(payload)

    # def _process_receive(self, payload):
    #     self._receive_ready = False
    #     self._receive_callback(payload)

    def send(self, payload, callback):
        self._finish_send_callback = callback

        assert 'dst' in payload and 'data_size' in payload
        payload['src'] = self._interface_id

        self._bus.sender_create_request(payload)

    def forbid_receive(self):
        self._receive_ready = False

    def allow_receive(self):
        self._receive_ready = True
        self._bus.recevier_issue_request(self._interface_id)

    def finish_send(self):
        if callable(self._finish_send_callback):
            self._finish_send_callback()

    def set_bus(self, bus):
        self._bus = bus

    @property
    def interface_id(self):
        return self._interface_id

    @property
    def receive_ready(self):
        return self._receive_ready

    def __mod__(self, other):
        if isinstance(other,MessageBus):
            other.__mod__(self)
        raise "Error Operator"

    def add_callback(self,func):
        self._receive_callback.add_func(func)


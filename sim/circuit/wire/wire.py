from __future__ import annotations

from sim.circuit.wire.base_wire import BaseWire
from sim.des.event import Event
from sim.des.simulator import Simulator
from sim.des.stime import Stime
from sim.des.utils import fl


# class UniChannel:
#     def __init__(self, wire: BaseWire):
#         self._wire = wire
#
#         self._payload = None
#         self._next_payload = None
#
#         self._sim: Simulator = self._wire.sim
#
#     def read_value(self):
#         return self._payload
#
#     def write_value(self, payload):
#         self._next_payload = payload
#         self._sim.add_event(Event(None, self.update_value, self._sim.next_update_epsilon))
#
#     def update_value(self):
#         if self._next_payload != self._payload:
#             self._payload = self._next_payload
#
#             self._sim.add_event(Event(None, self._wire.channel_callback, self._sim.next_handle_epsilon))


# class UniPulseChannel(UniChannel):
#     def __init__(self, wire):
#         super(UniPulseChannel, self).__init__(wire)
#
#         self._update_time = Stime(0, 0)
#
#         self._next_run_time = Stime(0, 0)
#
#     def read_value(self):
#         return self._payload
#
#     def update_value(self):
#         if self._next_payload != self._payload:
#             self._payload = self._next_payload
#             self._update_time = self._sim.current_time
#             self._sim.add_event(Event(None, self._wire.channel_callback, self._sim.next_handle_epsilon))
#
#             self.run_next()
#
#     def set_to_default(self):
#         if self._update_time.tick != self._sim.current_time.tick:
#             self._payload = None
#             self._update_time = self._sim.current_time
#             self._sim.add_event(Event(None, self._wire.channel_callback, self._sim.next_handle_epsilon))
#
#     def run_next(self):
#         if not self.is_run_next():
#             self._sim.add_event(Event(None, self.set_to_default, self._sim.next_tick))
#             self._next_run_time = self._sim.next_tick
#
#     def is_run_next(self) -> bool:
#         next_time = self._sim.next_tick
#         if self._next_run_time == next_time:
#             return True
#         return False


class UniWire(BaseWire):
    def __init__(self, sim, compo, readable=True, writeable=True, as_io_wire=False):
        super(UniWire, self).__init__(sim, compo)

        # self._channel = UniChannel(self)

        self._payload = None
        self._next_payload = None

        self._callbacks = fl()

        self._readable = readable
        self._writeable = writeable

        self._as_io_wire = as_io_wire

    def init(self,payload):
        #  仅初始化值，不调用回调函数
        #  对于OutWire来说，可以使用write初始化，对于内部的wire或者reg使用init初始化
        self._payload = payload

    def write(self, payload):
        assert self._writeable
        self.write_value(payload)

    def read(self):
        assert self._readable
        return self._payload

    def add_callback(self, *args):
        self._callbacks.add_func(*args)

    # force仅限 端口连接使用，跳过一个epsilon的更新
    def force_read(self):
        return self._payload

    def force_write(self, payload):
        self._next_payload = payload
        self.update_value()

    def write_value(self, payload):
        self._next_payload = payload
        self.make_event(self.update_value, self.next_update_epsilon)

    def update_value(self):
        if self._next_payload != self._payload:
            self._payload = self._next_payload
            self.make_event(self.run_callback, self.next_handle_epsilon)

    def run_callback(self):
        self._callbacks()

    def set_readable(self, readable):
        self._readable = readable

    def set_writeable(self, writeable):
        self._writeable = writeable

    def __rshift__(self, other: UniWire):
        if isinstance(other, BaseWire):
            self.add_callback(lambda: other.force_write(self.force_read()))
            other.set_writeable(False)
        else:
            raise "error"

    def __lshift__(self, other: UniWire):
        if isinstance(other, BaseWire):
            other.add_callback(lambda: self.force_write(other.force_read()))
            self.set_writeable(False)
        else:
            raise "error"

    @property
    def readable(self):
        return self._readable

    @property
    def writeable(self):
        return self._writeable

    @property
    def as_io_wire(self):
        return self._as_io_wire


# class UniPulseWire(UniWire):
#     def __init__(self, sim, compo, readable=True, writeable=True, as_io_wire=False):
#         super(UniPulseWire, self).__init__(sim, compo, readable, writeable, as_io_wire)
#
#         self._channel = UniPulseChannel(self)


def InWire(wire_class, sim, compo) -> UniWire:
    return wire_class(sim, compo, readable=True, writeable=False, as_io_wire=True)


def OutWire(wire_class, sim, compo) -> UniWire:
    return wire_class(sim, compo, readable=False, writeable=True, as_io_wire=True)

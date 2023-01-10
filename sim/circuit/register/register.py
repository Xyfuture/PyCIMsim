from __future__ import annotations

from sim.circuit.register.base_register import BaseRegister
from sim.circuit.wire.wire import InWire, UniWire, OutWire, UniPulseWire
from sim.des.base_compo import BaseCompo
from sim.des.stime import Stime
from sim.des.utils import fl


class RegNext(BaseRegister):
    '''
    普通的寄存器，当输入数据有变化时，下个周期数据变化
    不带enable端口
    '''

    def __init__(self, sim, compo):
        super(RegNext, self).__init__(sim, compo)

        self._payload = None
        self._update_time = None

        self._next_run_time = Stime(0, 0)

        # self._input_wire = InWire(UniWire, sim, self)
        # self._input_wire.add_callback(self.process_input)
        # self._output_wire = OutWire(UniWire, sim, self)

        # 想修改回只用一条线的模式
        self._input_wire = None
        self._output_wire = None

    def init(self, payload):
        self._payload = payload
        self._update_time = self.current_time

        self._output_wire.write(self._payload)

    def pulse(self):
        if self._input_wire.read() != self._payload:
            self._update_time = self.current_time
            self._payload = self._input_wire.read()

            self._output_wire.write(self._payload)

    def process_input(self):
        if self._input_wire.read() != self._payload:
            self.run_next()

    def run_next(self):
        if not self.is_run_next():
            next_time = self.next_tick
            self.make_event(self.pulse, next_time)

            self._next_run_time = next_time

    def is_run_next(self) -> bool:
        next_time = self.next_tick
        if self._next_run_time == next_time:
            return True
        return False

    def connect(self, input_wire: UniWire, output_wire: UniWire):
        # self._input_wire << input_wire
        # self._output_wire >> output_wire

        self._input_wire = input_wire
        self._output_wire = output_wire

        self._input_wire.add_callback(self.process_input)


class RegEnable(BaseRegister):
    '''
    基于RegNext，但是支持enable端口，可以打开关闭
    '''

    def __init__(self, sim, compo: BaseCompo):
        super(RegEnable, self).__init__(sim, compo)

        self._payload = None
        self._enable_payload = None
        self._update_time = None

        self._next_run_time = Stime(0, 0)

        # self._input_wire = InWire(UniWire, sim, self)
        # self._input_wire.add_callback(self.process_input)
        # self._output_wire = OutWire(UniWire, sim, self)
        #
        # self._enable_wire = InWire(UniWire, sim, self)
        # self._enable_wire.add_callback(self.process_enable)

        self._input_wire = None
        self._output_wire = None
        self._enable_wire = None

    def init(self, payload):
        self._payload = payload
        self._update_time = self.current_time

    def pulse(self):
        if self._enable_wire.read():
            if self._input_wire.read() != self._payload:
                self._payload = self._input_wire.read()
                self._update_time = self.current_time

                self._output_wire.write(self._payload)

    def process_input(self):
        if self._input_wire.read() != self._payload:

            self.run_next()

    def process_enable(self):
        if self._enable_wire.read():
            self.run_next()

    def run_next(self):
        if not self.is_run_next():
            next_time = self.next_tick
            self.make_event(self.pulse, next_time)

            self._next_run_time = next_time

    def is_run_next(self) -> bool:
        next_time = self.next_tick
        if self._next_run_time == next_time:
            return True
        return False

    def connect(self, input_wire: UniWire, enable_wire: UniWire, output_wire: UniWire):
        # self._input_wire << input_wire
        # self._output_wire >> output_wire
        # self._enable_wire << enable_wire

        self._input_wire = input_wire
        self._output_wire = output_wire
        self._enable_wire = enable_wire

        self._input_wire.add_callback(self.process_input)
        self._enable_wire.add_callback(self.process_enable)


class Trigger(BaseRegister):
    def __init__(self, sim, compo):
        super(Trigger, self).__init__(sim, compo)
        self._next_status = False

        self._payload = None
        self._update_time = None

        self._next_run_time = Stime(0, 0)

        # self._input_wire = InWire(UniPulseWire, sim, self)
        # self._input_wire.add_callback(self.process_input)

        self._input_wire = None

        self._callbacks = fl()

    def pulse(self):
        if self._payload:
            self.make_event(self._callbacks, self.next_handle_epsilon)

    def process_input(self):
        self._payload = self._input_wire.read()
        self.run_next()

    def run_next(self):
        if not self.is_run_next():
            next_time = self.next_tick
            self.make_event(self.pulse, next_time)

            self._next_run_time = next_time

    def is_run_next(self) -> bool:
        next_time = self.next_tick
        if self._next_run_time == next_time:
            return True
        return False

    def add_callback(self, func):
        self._callbacks.add_func(func)

    def connect(self, input_wire: UniWire):
        # self._input_wire << input_wire
        self._input_wire = input_wire
        self._input_wire.add_callback(self.process_input)

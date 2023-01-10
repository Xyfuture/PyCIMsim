from sim.des.base_compo import BaseCompo


class BaseWire(BaseCompo):
    def __init__(self, sim, compo):
        super(BaseWire, self).__init__(sim,compo)

    @property
    def readable(self):
        return False

    @property
    def writeable(self):
        return False

    @property
    def as_input(self):
        if self.as_io_wire:
            if self.readable:
                return True
        return False

    @property
    def as_output(self):
        if self.as_io_wire:
            if self.writeable:
                return True
        return False

    @property
    def as_io_wire(self):
        return False

    def channel_callback(self):
        pass

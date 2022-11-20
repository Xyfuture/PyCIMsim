from sim.des.base_element import BaseElement


class BaseWire(BaseElement):
    def __init__(self, compo):
        super(BaseWire, self).__init__(compo)

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

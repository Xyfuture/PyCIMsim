import queue
from sim.des.base_compo import BaseCompo
from sim.des.base_element import BaseElement

# unused 

class SwitchPort(BaseElement):
    def __init__(self,compo,input_handler):
        super(SwitchPort, self).__init__(compo)

        self._input_queue = queue.Queue()
        self._output_queue = queue.Queue()

        self._input_handler = input_handler
        self._channel = None

    def handle_input(self):
        if not self._input_queue.empty():
            payload = self._input_queue.get()
            if callable(self._input_handler):
                self._input_handler(payload)



    def read(self):
        pass

    def write(self,payload):
        pass

    def send_out(self):
        pass

    def receive_in(self,payload):
        pass

    def set_channel(self,channel):
        self._channel = channel




class SwitchChannel:
    def __init__(self):
        pass


class Switch(BaseCompo):
    def __init__(self,sim):
        super(Switch, self).__init__(sim)



class SwitchInterface(BaseElement):
    def __init__(self,compo):
        super(SwitchInterface, self).__init__(compo)

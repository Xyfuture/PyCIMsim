from sim.des.event import Event


class BaseElement:
    def __init__(self,compo):
        self._compo = compo
        self._sim = self._compo.sim

    def make_event(self,handler,time):
        event = Event(self._compo,handler,time)
        self.add_event(event)

    def add_event(self,ent):
        self._sim.add_event(ent)

    @property
    def current_time(self):
        return self._sim.current_time

    @property
    def next_tick(self):
        return self._sim.next_tick
    @property
    def next_epsilon(self):
        return self._sim.next_epsilon

    @property
    def next_update_epslion(self):
        return self._sim.next_update_epsilon

    @property
    def next_handle_epsilon(self):
        return self._sim.next_handle_epsilon
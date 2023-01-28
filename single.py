from sim.chip.chip import Chip
from sim.config.config import ChipConfig
from sim.core.inst.loader import load_dict
from sim.des.simulator import Simulator
import pickle
from threading import Thread


def print_info():
    while True:
        a = input()
        if a == 'end':
            break
        chip.get_running_status()


sim = Simulator()

chip_config = ChipConfig(
    core_cnt=1
)
chip = Chip(sim, chip_config)

pkl_path = 'program/resnet18_no_sync.pkl'
with open(pkl_path, 'rb') as f:
    inst_list = pickle.load(f)

print('start')
chip.read_inst_buffer_list([inst_list[0]])

t = Thread(target=print_info)
# t.start()


sim.initialize()
sim.run()

print(sim.event_cnt)

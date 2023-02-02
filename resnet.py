from sim.chip.chip import Chip
from sim.config.config import ChipConfig
from sim.core.inst.loader import load_dict
from sim.des.simulator import Simulator
import pickle
from threading import Thread


def print_info():
    while True:
        a = input()
        chip.get_running_status()


sim = Simulator()

chip_config = ChipConfig(
    core_cnt=129
)
chip = Chip(sim, chip_config)

pkl_path = 'program/resnet18_only_sync.pkl'
with open(pkl_path, 'rb') as f:
    inst_list = pickle.load(f)

print('start')
chip.read_inst_buffer_list(inst_list)

t = Thread(target=print_info)
# t.start()

sim.initialize()
sim.run()
# sim.new_run()

print(sim.event_cnt)


# print(chip.get_running_status())

from sim.chip.chip import Chip
from sim.config.config import ChipConfig
from sim.core.inst.loader import load_dict
from sim.des.simulator import Simulator
import pickle

if __name__ == '__main__':
    sim = Simulator()


    chip_config = ChipConfig(
        core_cnt=129
    )
    chip = Chip(sim, chip_config)

    # inst_list = []
    # for i in range(129):
    #     inst_list.append(load_dict(f"D:\\code\\test\\resnet18\\core{i}.txt"))

    with open('./resnet18.pkl','rb') as f:
        inst_list = pickle.load(f)

    print('start')
    chip.read_inst_buffer_list(inst_list)

    sim.initialize()
    sim.run()

    print(sim._event_cnt)

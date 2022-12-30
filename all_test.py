from sim.chip.chip import Chip
from sim.config.config import ChipConfig
from sim.core.inst.loader import load_dict
from sim.des.simulator import Simulator

if __name__ == '__main__':
    sim = Simulator()

    # chip_config = ChipConfig(
    # core_layout = (1, 1),
    # core_cnt=1
    # )
    # chip = Chip(sim,chip_config)
    #
    # inst = load_dict('program/core1.txt')
    # # inst = inst[75200:]
    # chip.read_inst_buffer_list([inst])

    chip_config = ChipConfig(
        core_cnt=129
    )
    chip = Chip(sim, chip_config)

    inst_list = []
    for i in range(129):
        inst_list.append(load_dict(f"D:\\code\\test\\resnet18\\core{i}.txt"))

    print('start')
    chip.read_inst_buffer_list(inst_list)

    sim.initialize()
    sim.run()

    print(sim._event_cnt)
    # chip.core_list[0].inst_fetch.get_running_status()
    # chip.core_list[0].transfer.get_running_status()

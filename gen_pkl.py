import pickle

from sim.core.inst.loader import *

inst_list = []

inst_dir = f"D:\\code\\test\\resnet18\\"
pkl_path = "program/resnet18.pkl"

filters = [sync_filter]

for i in range(129):
    inst_list.append(load_dict(inst_dir+f"core{i}.txt",[]))

with open(pkl_path,'wb') as f:
    pickle.dump(inst_list,f)

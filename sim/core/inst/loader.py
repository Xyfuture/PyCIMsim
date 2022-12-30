import json


def load_dict(file_path):
    inst = []
    with open(file_path, 'r') as f:
        for line in f.readlines():
            tmp = json.loads(line)
            if inst_filter(tmp):
                inst.append(convert(tmp))
    return inst


def convert(inst: dict):
    op = inst['opcode']

    tmp = inst
    tmp['op'] = tmp['opcode']

    if op == 'g2l':
        tmp = {
            'op': 'global_to_local', 'dst_addr': inst['dst'], 'src_addr': inst['src'],
            'data_size': inst['size']
        }
    elif op == 'l2g':
        tmp = {
            'op': 'local_to_global', 'dst_addr': inst['dst'], 'src_addr': inst['src'],
            'data_size': inst['size']
        }
    elif op == 'gemv':
        tmp = {
            'op': 'gemv', 'out_addr': inst['out_addr'], 'vec_addr': inst['vec_addr'],
            'pe_assign': ((inst['pe_assign_x'], inst['pe_assign_y']),
                          (inst['pe_assign_m'], inst['pe_assign_n'])), 'relu': False
        }
    elif op == 'g2d':
        tmp = {
            'op': 'global_to_dram', 'dst_addr': inst['dst'], 'src_addr': inst['src'],
            'data_size': inst['size']
        }
    elif op == 'd2g':
        tmp = {
            'op': 'dram_to_local', 'dst_addr': inst['dst'], 'src_addr': inst['src'],
            'data_size': inst['size']
        }
    elif op == 'global_cpy':
        tmp = {
            'op': 'global_cpy', 'dst_addr': inst['dst'], 'src_addr': inst['src'],
            'data_size': inst['size']
        }
    elif op == 'local_cpy':
        tmp = {
            'op': 'local_cpy', 'dst_addr': inst['dst'], 'src_addr': inst['src'],
            'data_size': inst['size']
        }
    elif op == 'g_clr':
        tmp = {
            'op': 'global_clr', 'dst_addr': inst['addr'],
            'data_size': inst['size']
        }
    elif op == 'l_clr':
        tmp = {
            'op': 'local_clr', 'dst_addr': inst['addr'],
            'data_size': inst['size']
        }
    else:
        if 'type' in tmp:
            tmp['act_type'] = tmp['type']

        if 'in_addr' in tmp:
            tmp['in1_addr'] = tmp['in_addr']

        if 'len' in tmp:
            tmp['vec_len'] = tmp['len']

    return tmp


def inst_filter(inst:dict):
    if inst['opcode'] == 'wait_core' or inst['opcode'] == 'sync':
        return False
    return True
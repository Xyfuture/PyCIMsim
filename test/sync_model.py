from __future__ import annotations

import pickle
import queue


class SyncCore:
    def __init__(self, core_id, inst_dict, chip):
        self.core_id = core_id
        self.inst_dict = inst_dict
        self.inst_len = len(inst_dict)

        self.state = 0  # inc_state
        self.wait_core_dict = {}

        self.sync_core_list = []

        self.chip: SyncChip = chip

        self.core_state = 'idle'  # sync wait_core finish
        self.pc = 0

    @property
    def cur_inst(self):
        return self.inst_dict[self.pc]

    @property
    def is_master_sync_core(self):
        if self.core_state == 'sync' and self.cur_inst['op'] == 'sync' and self.cur_inst['start_core'] == self.core_id:
            return True
        return False

    def run_tick(self):
        if self.core_state == 'idle':
            inst = self.inst_dict[self.pc]

            op = inst['opcode']
            if op == 'sync':
                self.core_state = 'sync'
                if self.is_master_sync_core:
                    start_core = self.cur_inst['start_core']
                    end_core = self.cur_inst['end_core']
                    if start_core == end_core:
                        self.update_pc()
                    else:
                        self.sync_core_list = [i for i in range(start_core + 1, end_core + 1)]
                        for core in self.sync_core_list:
                            message = {
                                'src': self.core_id, 'dst': core, 'info': {
                                    'op': 'sync', 'status': 'query', 'master_core': self.core_id
                                }
                            }
                            self.chip.forward_message_registry(message)
                else:
                    self.slave_sync_start()
            elif op == 'wait_core':
                self.core_state = 'wait_core'
                wait_core_id = inst['core_id']
                wait_state = inst['state']

                message = {
                    'src': self.core_id, 'dst': wait_core_id, 'info': {
                        'op': 'wait_core', 'state': wait_state, 'status': 'start'
                    }
                }

                self.chip.forward_message_registry(message)
            elif op == 'inc_state':
                self.state += 1
                self.activate_wait_core()
                self.update_pc()
            else:
                assert False

    def activate_wait_core(self):
        finish_wait_core = []
        for k, v in self.wait_core_dict.items():
            if v <= self.state:
                finish_wait_core.append(k)
                message = {
                    'src': self.core_id, 'dst': k, 'info': {
                        'op': 'inc_state', 'status': 'finish'
                    }
                }
                self.chip.forward_message_registry(message)

        for k in finish_wait_core:
            self.wait_core_dict.pop(k)

    def sync_all(self):
        if not self.sync_core_list and self.core_state == 'sync' and self.is_master_sync_core:
            start_core = self.inst_dict[self.pc]['start_core']
            end_core = self.inst_dict[self.pc]['end_core']

            for core in range(start_core + 1, end_core + 1):
                message = {
                    'src': self.core_id, 'dst': core, 'info': {
                        'op': 'sync', 'status': 'finish'
                    }
                }
                self.chip.forward_message_registry(message)

            self.update_pc()

    def slave_sync_start(self):
        if self.core_state == 'sync':
            master_core = self.cur_inst['start_core']
            assert self.core_id != master_core
            message = {
                'src': self.core_id, 'dst': master_core, 'info': {
                    'op': 'sync', 'status': 'start'
                }
            }
            self.chip.forward_message_registry(message)

    def handle_message(self, message):
        op = message['info']['op']

        if op == 'wait_core':  # 其他节点发来wait 本节点回复
            wait_state = message['info']['state']
            wait_src = message['src']
            # assert wait_src not in self.wait_core_dict
            self.wait_core_dict[wait_src] = wait_state
            self.activate_wait_core()
        elif op == 'inc_state':  # 其他节点发来 inc 本节点完成
            # assert self.core_state == 'wait_core'
            if self.core_state == 'wait_core':
                self.update_pc()
        elif op == 'sync':
            src = message['src']
            info = message['info']

            if info['status'] == 'start':  # 其他节点开始执行
                if self.is_master_sync_core:  # 是主节点接收消息
                    if src in self.sync_core_list:
                        self.sync_core_list.remove(src)
                        self.sync_all()
                # 不是主节点无操作
            elif info['status'] == 'query':  # 被查询
                if self.core_state == 'sync':
                    if self.cur_inst['start_core'] == info['master_core']:  # 检查是否是同一条指令
                        self.slave_sync_start()  # 只在执行当条指令时回复
            elif info['status'] == 'finish':
                assert self.core_state == 'sync'
                assert not self.is_master_sync_core
                self.update_pc()
        else:
            assert False

    def update_pc(self):
        self.pc += 1
        self.core_state = 'idle'

        if self.pc >= self.inst_len:
            self.chip.core_finish_registry(self.core_id)
            self.core_state = 'finish'


class SyncChip:
    def __init__(self, core_cnt, inst_list):
        self.core_cnt = core_cnt
        self.inst_list = inst_list

        self.core_list = []
        self.running_core = {}
        self.finish_core = {}
        self.pend_finish_core = []

        self.message_queue = queue.Queue()

        for i in range(self.core_cnt):
            core = SyncCore(i, inst_list[i], self)
            self.core_list.append(core)

            self.running_core[i] = core

    def forward_message_registry(self, message):
        self.message_queue.put(message)

    def forward_message(self):
        while not self.message_queue.empty():
            message = self.message_queue.get()
            dst = message['dst']
            try:
                self.running_core[dst].handle_message(message)
            except:
                print('here')

    def core_finish_registry(self, core_id):
        self.pend_finish_core.append(core_id)

    def core_finish(self):
        for core_id in self.pend_finish_core:
            core = self.running_core.pop(core_id)
            self.finish_core[core_id] = core

            print(f"core:{core_id} finished")
        self.pend_finish_core = []

    def run_one_tick(self):
        for k, v in self.running_core.items():
            v.run_tick()

        self.forward_message()
        self.core_finish()

    def run_all(self):
        while self.running_core:
            self.run_one_tick()
            if self.check_stall():
                print('stall')

    def check_stall(self):
        for k, v in self.running_core.items():
            if v.core_state == 'idle':
                return False
        return True


if __name__ == "__main__":
    pkl_path = '../program/resnet18_only_sync.pkl'
    with open(pkl_path, 'rb') as f:
        inst_list = pickle.load(f)

    chip = SyncChip(129, inst_list)
    chip.run_all()
    # print('finish')

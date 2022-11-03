


template_dict = {
    "op":"gemv",
    "dst":123,
    "src_1":123,
    "src_2":123,
    "imm":123,
    "len":123,
    "size":123,
    "start_core":123,
    "end_core":123,
    "core_id":123,
    "state":123
}


class Instruction:
    def __init__(self,dict_:dict):
        for k,v in dict_.items():
            self.__setattr__(k,v)


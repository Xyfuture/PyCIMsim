


# single instruction
class Instruction:
    def __init__(self,inst_dict:dict):
        for k,v in inst_dict.items():
            setattr(self,k,v)

    def convert(self):
        pass 



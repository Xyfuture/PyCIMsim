


# single instruction
class Instruction:
    def __init__(self,binary_inst:int):
        self._inst:int = binary_inst

        self._op = self.parse_binary_unsigned(self._inst,)

    @staticmethod
    def parse_binary_unsigned(binary_inst:int,l,r):
        tmp = binary_inst >> r
        tmp = tmp & ( (1<<(l-r+1)) -1)
        return tmp





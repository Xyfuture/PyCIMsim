

class FunctionList:
    def __init__(self, *args):
        self._func_list = []
        for f in args:
            if callable(f):
                self._func_list.append(f)

    def __call__(self):
        for f in self._func_list:
            f()


fl = FunctionList




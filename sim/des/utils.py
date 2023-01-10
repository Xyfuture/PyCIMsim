
class FunctionList:
    def __init__(self, *args):
        self._func_list = []
        for f in args:
            if callable(f):
                self._func_list.append(f)

    def add_func(self, *args):
        for f in args:
            if callable(f):
                self._func_list.append(f)

    def __call__(self, *args):
        for f in self._func_list:
            f(*args)


fl = FunctionList

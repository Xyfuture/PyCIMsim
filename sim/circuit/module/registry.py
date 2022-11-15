from typing import List


def registry(sensitive: List[str]):
    def add_property(func):
        func._sensitive_list = sensitive
        return func

    return add_property


def registry_safe(input_sen: List[str], output_sen: List[str]):
    def add_property(func):
        def wrapper(self):
            args = [self]
            for port_name in input_sen:
                port = getattr(self, port_name)
                payload = port.read()
                args.append(payload)
            output = func(*args)
            for port_name, payload in zip(output_sen, output):
                port = getattr(self, port_name)
                port.write(payload)

        wrapper._sensitive_list = input_sen
        return wrapper

    return add_property

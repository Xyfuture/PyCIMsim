from typing import List


def registry(sensitive: List[str]):
    def add_property(func):
        func._sensitive_list = sensitive
        return func

    return add_property

from pydantic import BaseConfig


class CoreConfig(BaseConfig):
    matrix_latency:int = 1000 # 1000 cycle

    vector_width:int = 32 # 32 alus per vector unit
    vector_latency:int = 2 # each op for 2 cycles

    local_buffer_read_speed:int = 40 * 2**30 # 40GB/s
    local_buffer_write_speed:int = 30 * 2**30 # 30GB/s

    local_bus_speed:int = 50 * 2**30 # 50GB/s


class ChipConfig(BaseConfig):
    core_config:CoreConfig = CoreConfig()

    noc_speed:int = 10 * 2**30 # 10GB/s

    global_buffer_read_speed:int = 40 * 2**30 # 40GB/s
    global_buffer_write_speed:int = 30 * 2**30 # 30GB/s

    offchip_memory_read_speed:int = 10 * 2**30 # 10GB/s
    offchip_memory_write_speed:int = 8 * 2**30 # 8GB/s



class SimConfig(BaseConfig):
    pass

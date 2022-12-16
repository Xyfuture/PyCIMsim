from typing import Tuple

from pydantic import BaseModel


class MemoryConfig(BaseModel):
    data_width: int = 16  # Bytes

    write_latency: int = 10  # cycles
    write_energy: float = 1.0  # nJ

    read_latency: int = 8  # cycles
    read_energy: float = 1.0  # nJ


class BusConfig(BaseModel):
    bus_width: int = 15  # Bytes

    latency: int = 1  # cycles
    energy: float = 1.0  # nJ


class CoreConfig(BaseModel):
    # matrix unit
    matrix_latency: int = 1000  # cycles
    matrix_energy_per_pe: float = 1.0  # nJ

    # vector unit
    vector_width: int = 32  # alus per vector unit
    vector_latency: int = 2  # each op for 2 cycles
    vector_energy: float = 1.0  # nJ

    local_buffer: MemoryConfig = MemoryConfig(data_width=32)

    local_bus: BusConfig = BusConfig(bus_width=32)

    # others
    scalar_energy: float = 1.0  # pJ
    register_energy: float = 1.0
    inst_fetch_energy: float = 1.0
    inst_decode_energy: float = 1.0

    transfer_energy: float = 1.0



class ChipConfig(BaseModel):
    core_config: CoreConfig = CoreConfig()
    core_layout: Tuple[2] = (8, 8)

    noc_bus: BusConfig = BusConfig()

    global_memory: MemoryConfig = MemoryConfig()
    offchip_memory: MemoryConfig = MemoryConfig()


class SimConfig(BaseModel):
    pass

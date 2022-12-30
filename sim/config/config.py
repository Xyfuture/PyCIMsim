from typing import Tuple, Optional

from pydantic import BaseModel


class MemoryConfig(BaseModel):
    memory_size: int = 1024 * 1024  # Bytes
    data_width: int = 16  # Bytes

    write_latency: int = 10  # cycles
    write_energy: float = 1.0  # nJ

    read_latency: int = 8  # cycles
    read_energy: float = 1.0  # nJ


class BusConfig(BaseModel):
    bus_topology: str = 'shared'  # 'mesh'
    bus_width: int = 15  # Bytes

    latency: int = 1  # cycles/hop
    energy: float = 1.0  # nJ/hop

    layout: Optional[Tuple[int, int]] = None


class CoreConfig(BaseModel):
    # precision setting
    input_precision: int = 16  # bits
    weight_precision: int = 16  # bits

    # matrix unit
    matrix_latency: int = 1000  # cycles
    matrix_energy_per_pe: float = 1.0  # nJ
    device_precision: int = 2  # bits
    xbar_size: Tuple[int, int] = (128, 128)
    pe_layout: Tuple[int, int] = (32, 8)

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

    # mode
    use_32bit_inst: bool = False


class ChipConfig(BaseModel):
    core_config: CoreConfig = CoreConfig()
    core_layout: Tuple[int, int] = (16, 16)
    core_cnt: int = 256

    noc_bus: BusConfig = BusConfig(layout=core_layout)

    global_memory: MemoryConfig = MemoryConfig()
    offchip_memory: MemoryConfig = MemoryConfig()


class SimConfig(BaseModel):
    pass

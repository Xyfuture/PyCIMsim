from typing import Any, Optional, Tuple, Union

from sim.core.utils.payload.base import PayloadBase


class BusPayload(PayloadBase):
    src: Union[str, int]
    dst: Union[str, int]

    data_size: int = 0  # Bytes
    payload: Any = None


class MemoryRequest(PayloadBase):
    access_type: str  # write or read
    addr: Optional[int] = None
    data: Optional[Any] = None
    data_size: int = 0  # Bytes


# 读内存时返回的结果
class MemoryReadValue(PayloadBase):
    data: Optional[Any] = None


class ScalarInfo(PayloadBase):
    op: str
    pc: int
    ex: str = 'scalar'

    rs1_data: int
    rs2_data: int
    rd_addr: int


class VectorInfo(PayloadBase):
    op: str
    pc: int
    ex: str = 'vector'

    out_addr: int
    in1_addr: int
    in2_addr: Optional[int] = None
    vec_len: int = 0
    act_type: Optional[str] = None
    imm: Optional[int] = None


class SyncInfo(PayloadBase):
    start_core: Optional[int] = None
    end_core: Optional[int] = None

    state: Optional[int] = None
    core_id: Optional[int] = None


class MemAccessInfo(PayloadBase):
    dst_addr: int
    src_addr: Optional[int] = None
    data_size: int  # bytes


class TransferInfo(PayloadBase):
    op: str
    pc: int
    ex: str = 'transfer'

    sync_info: Optional[SyncInfo] = None
    mem_access_info: Optional[MemAccessInfo] = None


class MatrixInfo(PayloadBase):
    op: str
    pc: int
    ex: str = 'matrix'

    out_addr: int
    vec_addr: int
    pe_assign: Tuple[Tuple[int, int], Tuple[int, int]]
    relu: bool


# 与寄存器堆产生的交互
class RegFileReadRequest(PayloadBase):
    rs1_addr: int = 0
    rs2_addr: int = 0
    rd_addr: int = 0


class RegFileReadValue(PayloadBase):
    rs1_data: int = 0
    rs2_data: int = 0
    rd_data: int = 0


class RegFileWriteRequest(PayloadBase):
    rd_addr: int = 0
    rd_value: int = 0


# 同步时Sync指令传输的信息
class SyncMessage(PayloadBase):
    op: str
    message: str

    sync_cnt: Optional[int] = None  # for op == 'sync'
    state: Optional[int] = None  # for op == 'wait_core'

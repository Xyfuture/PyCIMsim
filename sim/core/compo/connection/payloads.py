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


# decode 之后的结果
class VectorInfo(PayloadBase):
    op: str
    pc: int
    ex: str = 'vector'

    dst_addr: int
    src1_addr: int
    src2_addr: Optional[int] = None
    len: int
    imm: Optional[int] = None


class TransferInfo(PayloadBase):
    op: str
    pc: int
    ex: str = 'transfer'

    dst_addr: Optional[int] = None
    src1_addr: Optional[int] = None
    len: int
    imm: Optional[int] = None  # send/recv dst/src core id


class MatrixInfo(PayloadBase):
    op: str
    pc: int
    ex: str = 'matrix'

    dst_addr: int
    src1_addr: int
    group_id: int
    xbar_cnt: int
    input_len: int
    output_len: int

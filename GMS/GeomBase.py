from dataclasses import dataclass
import struct


@dataclass
class GeomBase:
    """Class holds ZGeomBase class"""
    name_offset_in_buf: int
    unk_4: int
    unk_8: int
    unk_C: int
    unk_10: int
    type_id: int
    unk_18: int
    control: int
    unk_20: int
    unk_24: int
    unk_28: int
    unk_2C: int
    unk_30: int
    unk_34: int
    unk_38: int
    unk_3C: int
    unk_40: int
    unk_44: int
    unk_48: int
    unk_4C: int
    unk_50: int
    unk_54: int
    unk_58: int
    unk_5C: int

    @staticmethod
    def from_bytes(buffer: bytes):
        name_offset_in_buf: int
        unk_4: int
        unk_8: int
        unk_C: int
        unk_10: int
        type_id: int
        unk_18: int
        control: int
        unk_20: int
        unk_24: int
        unk_28: int
        unk_2C: int
        unk_30: int
        unk_34: int
        unk_38: int
        unk_3C: int
        unk_40: int
        unk_44: int
        unk_48: int
        unk_4C: int
        unk_50: int
        unk_54: int
        unk_58: int
        unk_5C: int

        name_offset_in_buf, unk_4, unk_8, unk_C, \
        unk_10, type_id, unk_18, control, \
        unk_20, unk_24, unk_28, unk_2C, \
        unk_30, unk_34, unk_38, unk_3C, \
        unk_40, unk_44, unk_48, unk_4C, \
        unk_50, unk_54, unk_58, unk_5C = struct.unpack('<iiiiiiiiiiiiiiiiiiiiiiii', buffer)
        return GeomBase(name_offset_in_buf, unk_4, unk_8, unk_C,
                        unk_10, type_id, unk_18, control,
                        unk_20, unk_24, unk_28, unk_2C,
                        unk_30, unk_34, unk_38, unk_3C,
                        unk_40, unk_44, unk_48, unk_4C,
                        unk_50, unk_54, unk_58, unk_5C)

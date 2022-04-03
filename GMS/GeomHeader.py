from typing import Optional

from PRP import PRPInstruction
from GMS import GeomBase


class GeomHeader:
    def __init__(self, offset: int, unk4: int):
        self._offset: int = offset
        self._unk4: int = unk4
        self._name: str = ""
        self._typeid: int = 0
        self._geom_base: Optional[GeomBase] = None
        self._properties: [PRPInstruction] = []

    @staticmethod
    def _read_c_string_at(where: bytes, offset: int) -> str:
        chars: [str] = []
        current_offset: int = offset
        while True:
            c = chr(where[current_offset])
            current_offset += 1
            if c == chr(0):
                return "".join(chars)

            chars.append(c)

    def from_buffer(self, gms_buffer: bytes, buf_buffer: bytes):
        self_address: int = 4 * (self._offset & 0xFFFFFF)
        self._geom_base = GeomBase.from_bytes(gms_buffer[self_address: self_address + 0x60])
        self._name = GeomHeader._read_c_string_at(buf_buffer, self._geom_base.name_offset_in_buf)

    @property
    def geom_base(self) -> Optional[GeomBase]:
        return self._geom_base

    @property
    def name(self) -> str:
        return self._name

    @property
    def type_id(self) -> int:
        return self._typeid

    @property
    def depth_level(self) -> int:
        return self._offset >> 25

    @property
    def offset(self) -> int:
        return self._offset

    # Geom Props
    def _get_properties(self) -> [PRPInstruction]:
        return self._properties

    def _set_properties(self, new_props: [PRPInstruction]):
        self._properties = new_props

    geom_properties = property(_get_properties, _set_properties)
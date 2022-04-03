from GMS import GeomHeader

import struct


class GeomTable:
    def __init__(self, gms_buffer: bytes, buf_buffer: bytes):
        self._ent_list: [GeomHeader] = []

        # 1. Read offset of table
        self._table_offset: int = struct.unpack('<i', gms_buffer[0: 4])[0]

        # 2. Jump to table by offset and read count of entries
        self._ent_count: int = struct.unpack('<i', gms_buffer[self._table_offset: self._table_offset + 4])[0]

        # 3. Iterate over entries
        for ent_id in range(0, self._ent_count):
            entry_size: int = 8
            ent_addr: int = self._table_offset + 4 + (ent_id * entry_size)
            ent_decl_offset, ent_decl_unk4 = struct.unpack('<ii', gms_buffer[ent_addr: ent_addr + entry_size])

            ent_header: GeomHeader = GeomHeader(ent_decl_offset, ent_decl_unk4)
            ent_header.from_buffer(gms_buffer, buf_buffer)
            self._ent_list.append(ent_header)

    @property
    def entries(self) -> [GeomHeader]:
        return self._ent_list

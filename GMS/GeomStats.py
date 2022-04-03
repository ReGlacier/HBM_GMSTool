import struct

from GMS import GeomStat


class GeomStats:
    def __init__(self, gms_buffer: bytes):
        stats_begin_at: int = struct.unpack('<i', gms_buffer[0x10:0x14])[0]
        stats_data: bytes = gms_buffer[stats_begin_at:]

        self._stats = []

        stats_count: int = struct.unpack('<i', stats_data[0:4])[0]
        stat_idx: int

        for stat_idx in range(0, stats_count):
            type_id: int
            count: int
            unk8: int
            type_id, count, unk8 = struct.unpack('<ili', stats_data[4 + (stat_idx * 0xC): 4 + ((stat_idx + 1) * 0xC)])
            self._stats.append(GeomStat(type_id, count, unk8))

    @property
    def stats(self) -> [GeomStat]:
        return self._stats

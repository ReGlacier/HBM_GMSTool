class GeomStat:
    def __init__(self, type_id: int, count: int, unk8: int):
        self._type_id = type_id
        self._count = count
        self._unk8 = unk8

    @property
    def type_id(self) -> int:
        return self._type_id

    @property
    def count(self) -> int:
        return self._count

    @property
    def unk8(self) -> int:
        return self._unk8

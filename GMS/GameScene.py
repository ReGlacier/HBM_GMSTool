from PRP import PRPReader

from .GeomTable import GeomTable
from .GeomStats import GeomStats
from .GeomHeader import GeomHeader
from .GeomPropertiesVisitor import GeomPropertiesVisitor

from GMS.TDB.TypeDataBase import TypeDataBase

from typing import Optional, Any

import logging
import struct
import json
import zlib


class GameScene:
    def __init__(self, gms_path: str, buf_path: str, prp_path: str, tdb_path: str):
        self._gms_path: str = gms_path
        self._buf_path: str = buf_path
        self._prp_path: str = prp_path
        self._tdb_path: str = tdb_path

        self._gms_buffer: bytes = bytes()
        self._buf_buffer: bytes = bytes()
        self._gms_geom_table: Optional[GeomTable] = None
        self._gms_geom_stats: Optional[GeomStats] = None

        self._prp_reader: PRPReader = PRPReader(prp_path)
        self._tdb: TypeDataBase = TypeDataBase(tdb_path)

        self._scene_props: Any = None

    def prepare(self) -> bool:
        # Read GMS
        try:
            # Load & decompress GMS body
            with open(self._gms_path, "rb") as gms_file:
                whole_gms: bytes = gms_file.read()
                uncompressed_size, buffer_size, is_not_compressed = struct.unpack('<iib', whole_gms[0:9])
                is_compressed = not is_not_compressed

                if is_compressed:
                    real_size: int = (uncompressed_size + 15) & 0xFFFFFFF0
                    self._gms_buffer = zlib.decompress(whole_gms[9:], wbits=-15, bufsize=real_size)
                else:
                    self._gms_buffer = whole_gms[9:]
        except Exception as of_ex:
            print(f"Failed to open GMS file {self._gms_path}. Reason: {of_ex}")
            return False

        # Read BUF
        try:
            with open(self._buf_path, "rb") as buf_file:
                self._buf_buffer = buf_file.read()
        except Exception as of_ex:
            print(f"Failed to open BUF file {self._buf_path}. Reason: {of_ex}")
            self._gms_buffer = bytes()
            return False

        # Read properties
        try:
            self._prp_reader.parse()
        except Exception as e:
            print(f"Failed to prepare PRP file {self._prp_path}. Reason: {e}")
            return False

        # Prepare types database
        if not self._tdb.load():
            print(f"Failed to load types database from file {self._tdb_path}")
            return False

        # Prepare GMS body
        return self._prepare_gms()

    def dump(self, out_file: str) -> bool:
        if self._scene_props is None:
            return False

        try:
            with open(out_file, "w") as out_scene_file:
                print("Dumping to json... (it's very slow process, cuz Python is so stupid)")
                scene_dump: dict = dict()
                scene_dump["flags"] = self._prp_reader.flags
                scene_dump["is_raw"] = self._prp_reader.is_raw
                scene_dump["defines"] = [x.__dict__() for x in self._prp_reader.definitions]
                scene_dump["scene"] = self._scene_props

                json.dump(scene_dump, out_scene_file, indent=2)
                print(f"Scene dump saved to file {out_file} successfully!")
                return True
        except IOError as ioe:
            print(f"Failed to save scene file to {out_file}. IOError: {ioe}")
            return False

    @property
    def properties(self) -> PRPReader:
        return self._prp_reader

    @property
    def geoms(self) -> [GeomHeader]:
        return self._gms_geom_table.entries

    @property
    def geom_stats(self) -> GeomStats:
        return self._gms_geom_stats

    @property
    def type_db(self) -> TypeDataBase:
        return self._tdb

    def _prepare_gms(self) -> bool:
        # Load entries
        self._gms_geom_table = GeomTable(self._gms_buffer, self._buf_buffer)
        self._gms_geom_stats = GeomStats(self._gms_buffer)

        # Load properties for each entry
        visitor: GeomPropertiesVisitor = GeomPropertiesVisitor(self.geoms, self.properties)
        visited_geoms = visitor.visit(self.type_db, 'ROOT', GeomPropertiesVisitor.ZROOM)

        print(f" --- DECOMPILE FINISHED ({len(self.geoms)} GEOMS) --- ")
        print(f" Ignored instructions: {visitor.total_instructions - visitor.current_instruction - 1} (0 - 1 is OK; More - FAILURE)")

        self._scene_props = visited_geoms
        return True

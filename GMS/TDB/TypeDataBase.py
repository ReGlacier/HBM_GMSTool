from typing import Optional
from pathlib import Path

import json
import glob
import os


class TypeDataBase:
    def __init__(self, tdb_path: str):
        from GMS.TDB.Type import Type

        self._types: [Type] = []
        self._tdb_path: str = os.path.realpath(tdb_path)
        self._type_exports: dict = dict()

    def load(self):
        from GMS.TDB.Type import Type
        from GMS.TDB.TypeLink import TypeLink

        try:
            with open(self._tdb_path, "r") as tdb_file:
                jtdb = json.load(tdb_file)
                inc_path: str = os.path.realpath(jtdb['inc'])
                db_refs: dict = jtdb['db']

                # Iterate over JSON definitions
                inc_traverse_path = os.path.realpath(
                    os.path.join(os.path.split(self._tdb_path)[0], os.path.basename(inc_path)))
                filename: str
                for filename in glob.glob(inc_traverse_path + os.path.sep + '*.json', recursive=True):
                    with open(filename, "r") as type_definition_file:
                        j_type = json.load(type_definition_file)
                        type_def: Type = Type(j_type)
                        fn: str = Path(filename).stem
                        assert fn == type_def.name, \
                               f"Typename ({type_def.name}) and file name ({fn}) must be same, but they doesn't!"

                        self._types.append(type_def)

                # Resolve x-linking
                type_id: str
                for type_id in db_refs:
                    type_name: str = db_refs[type_id]
                    type_ref: Optional[Type] = self.find_type(type_name)
                    if type_ref is None:
                        raise RuntimeError(f"Unable to resolve link from typeid {type_id} to type by name {type_name}. Type not found")
                    else:
                        self._type_exports[type_id] = type_ref

                # And resolve linking
                current_type: Type
                for current_type in self._types:
                    if issubclass(type(current_type.data), TypeLink):
                        type_link_r: TypeLink = current_type.data
                        type_link_r.resolve_external_links(self)

                return True
        except Exception as ex:
            raise RuntimeError(f"Failed to tload {self._tdb_path}. Reason: {ex}")
            return False

    def find_type(self, typename: str):
        from GMS.TDB.Type import Type

        type_decl: Type
        for type_decl in self._types:
            if type_decl.name == typename or type_decl.name[1:] == typename:
                return type_decl

        return None

    def find_type_by_short_name(self, typename: str):
        from GMS.TDB.Type import Type

        type_decl: Type
        for type_decl in self._types:
            type_decl_name: str = type_decl.name

            # >>> IOI HACKS AREA STARTS HERE <<<
            # Simple compare
            if type_decl_name == typename:
                return type_decl

            # Hack #1: IOI G1 codegen remove Z & C prefix from typename
            if (type_decl_name[0] == 'Z' or type_decl_name[0] == 'C') and (type_decl_name[1:] == typename):
                return type_decl

            # Hack #2: IOI G1 codegen remove Event postfix from typename too
            if ((type_decl_name[0] == 'Z' or type_decl_name[0] == 'C') and type_decl_name.endswith('Event')) \
                    and (type_decl_name[1:-5] == typename):
                return type_decl

            # Hack #3: IOI G1 codegen for Hitman Blood Money (HM3) removing HM3 prefix
            if ((type_decl_name[0] == 'Z' or type_decl_name[0] == 'C') and type_decl_name[1:].startswith('HM3')) \
                    and (type_decl_name[4:] == typename):
                return type_decl
            # >>> END OF IOI HACKS AREA <<<

        return None

    def resolve_external_reference(self, reference: int):
        ref_s: str = '0x{:X}'.format(reference)
        if ref_s in self._type_exports:
            return self._type_exports[ref_s]
        else:
            return None

    @property
    def exported_types(self) -> dict:
        return self._type_exports

    @property
    def types(self):
        return self._types

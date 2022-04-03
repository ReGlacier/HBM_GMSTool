from PRP import PRPDefinition, PRPInstruction, PRPWriter, PRPOpCode
from GMS.TDB.TypeDataBase import TypeDataBase
from GMS.TDB.Type import Type
from typing import Any, Optional


class JsonSceneTreeVisitor:
    def __init__(self, scene: Any, tdb: TypeDataBase):
        self._scene = scene
        self._tdb: TypeDataBase = tdb

    def visit(self) -> [PRPInstruction]:
        entry = self._scene

        result: [PRPInstruction] = self._visit_ent(entry)
        result += [PRPInstruction(PRPOpCode.Bool, False), PRPInstruction(PRPOpCode.EndOfStream)]
        return result

    def _visit_ent(self, ent: Any) -> [PRPInstruction]:
        collected_instructions: [PRPInstruction] = [PRPInstruction(PRPOpCode.BeginObject)]

        for prop in ent["properties"]:
            property_type: str = prop["type"]
            property_name: str = prop["name"]
            property_owner: str = prop["owner"] if "owner" in prop else "(unknown)"
            property_value = prop["value"]

            if property_type.startswith("PRPOpCode."):
                prp_op_code: PRPOpCode = PRPOpCode[property_type.split('.')[1]]
                collected_instructions.append(PRPInstruction(prp_op_code, prop['value']))
            else:
                r_type: Optional[Type] = self._tdb.find_type(property_type)
                if r_type is None:
                    raise RuntimeError(f"Type {property_type} not found in types database. Unable to visit property {property_name}")

                if not r_type.check_value(property_value):
                    raise RuntimeError(f"For property {property_name} (of {property_owner}) value {property_value} "
                                       f"not valid!")

                collected_instructions += r_type.serialize_to_prp(property_value)

        collected_instructions += [PRPInstruction(PRPOpCode.EndObject),
                                   PRPInstruction(PRPOpCode.Container, {'length': len(ent["controllers"])})]
        for controller in ent["controllers"]:
            collected_instructions += self._visit_controller(controller)

        collected_instructions += [PRPInstruction(PRPOpCode.Container, {'length': len(ent["children"])})]
        for child in ent["children"]:
            collected_instructions += self._visit_ent(child)

        return collected_instructions

    def _visit_controller(self, controller) -> [PRPInstruction]:
        # Push controller name
        controller_name: str = controller["name"]

        collected_instructions: [PRPInstruction] = [PRPInstruction(PRPOpCode.String, {'length': len(controller["name"]),
                                                                                      'data': controller["name"]}),
                                                    PRPInstruction(PRPOpCode.BeginObject)]

        for prop in controller["properties"]:
            prop_type: str = prop["type"]

            if prop_type == 'unexposed_instruction':
                collected_instructions.append(PRPInstruction.from_json(prop["data"]))
            elif prop_type.startswith('PRPOpCode.'):
                collected_instructions.append(PRPInstruction(PRPOpCode[prop_type.split('.')[1]], prop['value'] if 'value' in prop else None))
            else:
                prop_name: str = prop["name"]
                prop_value = prop["value"]

                r_type: Optional[Type] = self._tdb.find_type(prop_type)
                if r_type is None:
                    raise RuntimeError(f"Failed to visit controller of type {controller_name}. "
                                       f"Type {prop_type} not found in types database")

                if not r_type.check_value(prop_value):
                    raise RuntimeError(f"For property {prop_name} of type {prop_type} value {prop_value} is not valid!")

                collected_instructions += r_type.serialize_to_prp(prop_value)

        collected_instructions.append(PRPInstruction(PRPOpCode.EndObject))
        return collected_instructions


class SceneCompiler:
    def __init__(self, j, tdb_path: str):
        self._json = j
        self._tdb: TypeDataBase = TypeDataBase(tdb_path)

    def compile(self, out_prp_file: str) -> bool:
        if not self._tdb.load():
            print("Failed to load types database file! See log for details")
            return False

        if "flags" not in self._json:
            print("Failed to compile PRP: JSON entry 'flags' is required!")
            return False

        if "is_raw" not in self._json:
            print("Failed to compile PRP: JSON entry 'is_raw' is required!")
            return False

        if "defines" not in self._json:
            print("Failed to compile PRP: JSON entry 'defines' is required!")
            return False

        if "scene" not in self._json:
            print("Failed to compile PRP: JSON entry 'scene' is required!")
            return False

        # 1. Extract Z-Defines
        z_defines: [PRPDefinition] = []
        flags: int = self._json["flags"]
        is_raw: bool = self._json["is_raw"]

        for json_zdef in self._json["defines"]:
            entry: PRPDefinition = PRPDefinition.from_json(json_zdef)
            z_defines.append(entry)

        json_scene_visitor: JsonSceneTreeVisitor = JsonSceneTreeVisitor(self._json["scene"], self._tdb)
        instructions: [PRPInstruction] = json_scene_visitor.visit()

        writer: PRPWriter = PRPWriter(out_prp_file)
        writer.write(flags, z_defines, instructions, is_raw)
        return True

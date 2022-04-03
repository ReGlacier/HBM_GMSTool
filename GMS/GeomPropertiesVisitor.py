from GMS import GeomHeader
from PRP import PRPReader, PRPOpCode

import GMS.TDB as TDB

from typing import Optional
from ctypes import c_ulong

import inspect


class GeomPropertiesVisitor:
    ZROOM = 0x100021

    def __init__(self, geoms: [GeomHeader], prp: PRPReader):
        self._geoms: [GeomHeader] = geoms
        self._prp: PRPReader = prp
        self._instruction_index = 0
        self._geom_index = -1

    @property
    def current_instruction(self) -> int:
        return self._instruction_index

    @property
    def total_instructions(self) -> int:
        return len(self._prp.instructions)

    def visit(self, tdb: TDB.TypeDataBase.TypeDataBase, geom_name: str = 'ROOT', geom_type: int = ZROOM) -> dict:
        if geom_type < 0:
            # Here we need to convert this value properly
            # TODO: Fix this bug on GeomHeader parser level!
            geom_type = c_ulong(geom_type).value

        print("Visit {} 0x{:X} (IP: {}, GI: {})".format(geom_name, geom_type, self._instruction_index, self._geom_index))
        from PRP import PRPInstruction, PRPOpCode

        result: dict = dict()

        r_type: Optional[TDB.Type.Type] = tdb.resolve_external_reference(geom_type)
        if r_type is None:
            raise RuntimeError("Failed to visit type 0x{:X} of name {}. No type in database".format(geom_type, geom_name))

        # We need to map next N instructions to our "properties"
        instructions: [PRPInstruction] = self._prp.instructions

        assert instructions[self._instruction_index].op_code == PRPOpCode.BeginObject or \
               instructions[self._instruction_index].op_code == PRPOpCode.BeginNamedObject

        self._instruction_index += 1  # Skip begin object

        next_instruction: int
        extracted_properties: []
        next_instruction, extracted_properties = r_type.visit(self._instruction_index, instructions, r_type.name)

        result['name'] = geom_name
        result['type'] = dict()
        result['type']['id'] = geom_type
        result['type']['name'] = r_type.name
        result['properties'] = extracted_properties
        result['controllers'] = []
        result['children'] = []

        assert instructions[next_instruction].op_code == PRPOpCode.EndObject, "Expected end of object after visiting object"
        next_instruction += 1

        self._instruction_index = next_instruction
        self._next_geom()

        # End of visiting our first entry. Now we ready to visit it's own controllers region
        # ---- READ CONTROLLERS ----
        assert instructions[self._instruction_index].op_code == PRPOpCode.Container, "Expected controllers region"
        if instructions[self._instruction_index].op_data['length'] > 0:
            controller_idx: int
            controllers_num: int = instructions[self._instruction_index].op_data['length']

            self._instruction_index += 1  # Move to first instruction

            for controller_idx in range(0, controllers_num):
                assert instructions[self._instruction_index].op_code == PRPOpCode.String, "Expected name of controller"
                controller_name_instruction_idx: int = self._instruction_index
                controller_name: str = instructions[controller_name_instruction_idx].op_data['data']
                self._instruction_index += 1

                assert instructions[self._instruction_index].op_code == PRPOpCode.BeginObject \
                       or instructions[self._instruction_index].op_code == PRPOpCode.BeginNamedObject, \
                       f"Expected begin object or begin named object with information about controller, " \
                       f"but got {instructions[self._instruction_index].op_code} " \
                       f"(instruction index {self._instruction_index}, geom index {self._geom_index})"

                # Skip BeginObject instruction
                self._instruction_index += 1

                controller_type: Optional[TDB.Type.Type] = tdb.find_type_by_short_name(controller_name)
                if controller_type is None:
                    raise RuntimeError(f"Failed to find controller of type {controller_name}. "
                                       f"Current instruction {self._instruction_index}")

                controller_next_instruction, controller_extracted_properties = controller_type.visit(self._instruction_index,
                                                                                                     instructions,
                                                                                                     controller_type.name)

                controller_info: dict = dict()
                controller_info['name'] = controller_name
                controller_info['properties'] = controller_extracted_properties

                result['controllers'].append(controller_info)

                self._instruction_index = controller_next_instruction  # Change instruction pointer, don't change geom index

                if instructions[self._instruction_index].op_code == PRPOpCode.EndObject:
                    self._instruction_index += 1  # Skip end of object
        else:
            self._instruction_index += 1

        # And here we ready to go deeper inside entity children
        # ---- READ CHILDREN GEOMS ----
        assert instructions[self._instruction_index].op_code == PRPOpCode.Container, "Expected children region"
        child_num: int = instructions[self._instruction_index].op_data['length']
        if child_num > 0:
            self._instruction_index += 1  # Jump to first object declaration

            assert instructions[self._instruction_index].op_code == PRPOpCode.BeginObject or \
                   instructions[self._instruction_index].op_code == PRPOpCode.BeginNamedObject, \
                   f"Expected begin object or begin named object, but got {instructions[self._instruction_index].op_code} (instruction index {self._instruction_index}, geom index {self._geom_index})"

            for geom_idx in range(0, child_num):
                instruction_index_before_visit_next_child: int = self._instruction_index
                current_geom: GeomHeader = self._geoms[self._geom_index]
                visited_geom = self.visit(tdb, current_geom.name, current_geom.geom_base.type_id)
                result['children'].append(visited_geom)
        else:
            self._instruction_index += 1

        # Here we working with next entry in the same layer (?)
        return result
    
    def _next_geom(self):
        cl_line_no, cl_callee = inspect.stack()[1][2:4]
        print(f" [from {cl_callee} at {cl_line_no}] Switch geom {self._geom_index} -> {self._geom_index + 1}")
        self._geom_index += 1

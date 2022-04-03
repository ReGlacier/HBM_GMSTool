from PRP import PRPInstruction, PRPOpCode

import GMS.TDB as TDB

from typing import Optional, Union


class ComplexProperty:
    ResolvedType = Union[TDB.Type.Type, PRPOpCode, None]

    def __init__(self, name: str, typename: str, offset: Optional[int] = None):
        self._name = name
        self._typename = typename
        self._offset = offset
        self._resolved_type: ComplexProperty.ResolvedType = None

    def set_type(self, rs_type: TDB.Type.Type):
        assert rs_type.name == self._typename

        self._resolved_type = rs_type

    def set_opcode(self, rs_opc: PRPOpCode):
        self._resolved_type = rs_opc

    @property
    def name(self) -> str:
        return self._name

    @property
    def typename(self) -> str:
        return self._typename

    @property
    def type_def(self) -> ResolvedType:
        return self._resolved_type

    @property
    def offset(self) -> Optional[int]:
        return self._offset


class TypeComplex(TDB.TypeLink.TypeLink, TDB.VisitableType.VisitableType):
    def __init__(self, props: [ComplexProperty], parent: Optional[str], skip_unexposed_properties: bool):
        super().__init__()

        self.properties = props
        self.parent: Union[str, TDB.Type.Type, None] = parent
        self.skip_unexposed_properties: bool = skip_unexposed_properties

    def resolve_external_links(self, tdb: TDB.TypeDataBase.TypeDataBase):
        if type(self.parent) is str:
            parent_type_name: str = self.parent
            self.parent = tdb.find_type(parent_type_name)
            if self.parent is None:
                raise RuntimeError(f"Failed to locate type {parent_type_name}. Please, make sure that this type exists!")

        prop: ComplexProperty
        for prop in self.properties:
            if not prop.typename.startswith('PRPOpCode.'):
                rs_type: Optional[TDB.Type.Type] = tdb.find_type(prop.typename)
                if rs_type is not None:
                    prop.set_type(rs_type)
                else:
                    raise RuntimeError(f"Failed to locate type by name {prop.typename}. Please, make sure that this type is valid and available in types database!")
            else:
                prop.set_opcode(PRPOpCode[prop.typename.split('.')[1]])

    def visit(self, current_instruction_index: int, instructions: [PRPInstruction], owner_typename: Optional[str]) -> (int, []):
        extracted_properties: [] = []
        if self.parent is not None:
            next_instru, parent_extracted_props = self.parent.visit(current_instruction_index,
                                                                    instructions,
                                                                    self.parent.name)

            if next_instru != -1:
                extracted_properties += parent_extracted_props
                current_instruction_index = next_instru
            else:
                raise RuntimeError("Failed to prepare parent type")

        prop: ComplexProperty
        for prop in self.properties:
            start_instruction: int = current_instruction_index

            if type(prop.type_def) is PRPOpCode:
                constructed_prop: dict = dict()
                if owner_typename is not None:
                    constructed_prop['owner'] = owner_typename

                constructed_prop['name'] = prop.name
                constructed_prop['type'] = prop.typename
                constructed_prop['value'] = instructions[current_instruction_index].op_data

                extracted_properties += [constructed_prop]
                current_instruction_index += 1
            elif type(prop.type_def) is TDB.Type.Type:
                next_instru, prop_extracted_props = prop.type_def.visit(current_instruction_index,
                                                                        instructions,
                                                                        owner_typename)
                if next_instru != -1:
                    constructed_prop: dict = dict()
                    if owner_typename is not None:
                        constructed_prop['owner'] = owner_typename

                    constructed_prop['name'] = prop.name
                    constructed_prop['type'] = prop.typename
                    constructed_prop['value'] = prop_extracted_props

                    extracted_properties += [constructed_prop]
                    current_instruction_index = next_instru
                else:
                    raise RuntimeError("Failed to prepare property")

        unexposed_instructions: [] = []
        if instructions[current_instruction_index].op_code != PRPOpCode.EndObject and self.skip_unexposed_properties:
            # Run skipping unexposed things until object ends
            object_depth: int = 1
            object_end_markers_found: int = 0

            while object_end_markers_found != object_depth:
                unexposed_instruction: dict = dict()
                if owner_typename is not None:
                    unexposed_instruction['owner'] = owner_typename

                unexposed_instruction['type'] = 'unexposed_instruction'
                unexposed_instruction['data'] = dict()
                unexposed_instruction['data']['op_code'] = str(instructions[current_instruction_index].op_code)
                unexposed_instruction['data']['op_data'] = instructions[current_instruction_index].op_data

                unexposed_instructions.append(unexposed_instruction)

                if instructions[current_instruction_index].op_code == PRPOpCode.BeginObject or \
                        instructions[current_instruction_index].op_code == PRPOpCode.BeginNamedObject:
                    object_depth += 1

                if instructions[current_instruction_index].op_code == PRPOpCode.EndObject:
                    object_end_markers_found += 1

                current_instruction_index += 1

            # Remove 'end object' marker from unexposed instructions
            if unexposed_instructions[-1]['data']['op_code'] == str(PRPOpCode.EndObject):
                unexposed_instructions.pop(-1)

            extracted_properties += unexposed_instructions

        return current_instruction_index, extracted_properties

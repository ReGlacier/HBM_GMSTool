from PRP import PRPInstruction, PRPOpCode

from typing import Optional, Union, Any
from enum import Enum

import GMS.TDB as TDB


class TypeKind(Enum):
    ENUM = 0,
    ALIAS = 1,
    COMPLEX = 2,
    ARRAY = 3,
    CONTAINER = 4,
    RAW_DATA = 5,
    BITFIELD = 6


class Type:
    ManagedType = Any

    def __init__(self, jd: dict):
        self._typename: str
        self._kind: TypeKind
        self._data: Type.ManagedType

        if 'kind' in jd:
            self._kind = TypeKind[jd['kind'].split('.')[1]]
        else:
            raise RuntimeError("Bad type definition! 'kind' field is required!")

        if 'typename' in jd:
            self._typename = jd['typename']
        else:
            raise RuntimeError("Bad type definition! 'typename' field is required!")

        if self._kind == TypeKind.ENUM:
            self._prepare_enum(jd)
        elif self._kind == TypeKind.ALIAS:
            self._prepare_alias(jd)
        elif self._kind == TypeKind.COMPLEX:
            self._prepare_complex(jd)
        elif self._kind == TypeKind.ARRAY:
            self._prepare_array(jd)
        elif self._kind == TypeKind.CONTAINER:
            self._prepare_container(jd)
        elif self.kind == TypeKind.RAW_DATA:
            self._prepare_raw_data(jd)
        elif self.kind == TypeKind.BITFIELD:
            self._prepare_bitfield(jd)
        else:
            raise RuntimeError("Unsupported type kind!")

    def _prepare_enum(self, jd: dict):
        if 'enum' in jd:
            self._data = TDB.TypeEnum.TypeEnum(jd['enum'])
        else:
            raise RuntimeError("Bad enum definition! 'enum' field is required!")

    def _prepare_alias(self, jd: dict):
        if 'alias' in jd:
            self._data = TDB.TypeAlias.TypeAlias(jd['typename'], jd['alias'])
        else:
            raise RuntimeError("Bad alias definition! 'alias' field is required!")

    def _prepare_complex(self, jd: dict):
        parent: Optional[str] = None
        skip_unexposed_properties: bool = False

        if 'parent' in jd:
            parent = jd['parent']

        if 'skip_unexposed_properties' in jd:
            # This flag means that visitors of TypeComplex will prepare all exposed properties
            # and skip all others until objects will not be ended.
            # Otherwise, it will raise an exception if unexposed instructions (properties)
            # will be in the object definition.
            skip_unexposed_properties = jd['skip_unexposed_properties']

        if 'properties' in jd:
            properties: [TDB.TypeComplex.ComplexProperty] = []
            props = jd['properties']
            prop: dict
            for prop in props:
                assert 'name' in prop
                assert 'typename' in prop

                name: str = prop['name']
                typename: str = prop['typename']
                offset: Optional[int] = None

                if 'offset' in prop:
                    offset = prop['offset']

                properties.append(TDB.TypeComplex.ComplexProperty(name, typename, offset))

            self._data = TDB.TypeComplex.TypeComplex(properties, parent, skip_unexposed_properties)
        else:
            raise RuntimeError("Bad complex type definition! 'properties' field is required!")

    def _prepare_array(self, jd: dict):
        if 'array' in jd:
            expected_length: Optional[int] = None
            inner_opcode_type: PRPOpCode
            transform: dict = dict()

            if 'expected_length' in jd['array']:
                expected_length = jd['array']['expected_length']

            if 'inner_opcode_type' in jd['array']:
                inner_opcode_type = PRPOpCode[jd['array']['inner_opcode_type'].split('.')[1]]
            else:
                raise RuntimeError("Bad array definition! 'inner_opcode_type' field is required")

            if 'transform' in jd:
                transform = jd['transform']

            self._data = TDB.TypeArray.TypeArray(expected_length, inner_opcode_type, transform)
        else:
            raise RuntimeError("Bad array definition! 'array' field is required!")

    def _prepare_container(self, jd: dict):
        self._data = TDB.TypeContainer.TypeContainer()

    def _prepare_raw_data(self, jd: dict):
        self._data = TDB.TypeRawData.TypeRawData()

    def _prepare_bitfield(self, jd: dict):
        if 'bitfield' in jd:
            if 'values' not in jd['bitfield']:
                raise RuntimeError("Bad bitfield definition! 'values' field is required!")

            if 'type' not in jd['bitfield']:
                raise RuntimeError("Bad bitfield definition! 'type' field is required!")

            values: dict = jd['bitfield']['values']
            v_type: str = jd['bitfield']['type']

            if not v_type.startswith('PRPOpCode.'):
                raise RuntimeError("Bad bitfield definition! 'type' field must be a member of PRPOpCode!")

            s_type: PRPOpCode = PRPOpCode[v_type.split('.')[1]]

            self._data = TDB.TypeBitfield.TypeBitfield(jd['typename'], values, s_type)
        else:
            raise RuntimeError("Bad bitfield definition! 'bitfield' field is required!")

    def visit(self, current_instruction_index: int, prp_instructions: [PRPInstruction], owner_typename: Optional[str]) -> (int, []):
        if self._data is not None:
            next_instruction: int
            extracted_props: []
            next_instruction, extracted_props = self._data.visit(current_instruction_index,
                                                                 prp_instructions,
                                                                 owner_typename)

            if next_instruction == -1:
                return -1, []

            # TODO: Support validation layer here

            return next_instruction, extracted_props

        return -1, []

    def serialize_to_prp(self, value: Any) -> [PRPInstruction]:
        if self._data is not None:
            return self._data.to_prp(value)

        raise RuntimeError(f"Unknown backend type of {self._typename}")

    def check_value(self, value: Any) -> bool:
        if self._data is not None:
            return self._data.check_value(value)

        raise RuntimeError(f"Unknown backend type of {self._typename}")

    @property
    def name(self) -> str:
        return self._typename

    @property
    def kind(self) -> TypeKind:
        return self._kind

    def _get_data(self) -> ManagedType:
        return self._data

    def _set_data(self, d: ManagedType):
        self._data = d

    data = property(_get_data, _set_data)

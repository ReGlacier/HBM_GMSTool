from GMS.TDB.VisitableType import VisitableType
from PRP import PRPInstruction, PRPOpCode
from typing import Optional, Any


class TypeEnum(VisitableType):
    def __init__(self, values: dict):
        self._values = values

    @property
    def values(self) -> dict:
        return self._values

    def visit(self, current_instruction_index: int, instructions: [PRPInstruction], owner_typename: Optional[str]) -> (int, []):
        current_instruction: PRPInstruction = instructions[current_instruction_index]

        assert current_instruction.op_code == PRPOpCode.StringOrArray_E or \
               current_instruction.op_code == PRPOpCode.StringOrArray_8E

        # if owner_typename is not None:
        #     ret_enum_obj['owner_type'] = owner_typename

        return current_instruction_index + 1, current_instruction.op_data['data']

    def to_prp(self, value: Any) -> [PRPInstruction]:
        return [PRPInstruction(PRPOpCode.StringOrArray_E, {'length': len(value), 'data': value})]

    def check_value(self, value: Any) -> bool:
        return value in self._values

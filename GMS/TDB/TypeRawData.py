from GMS.TDB.VisitableType import VisitableType
from PRP import PRPInstruction, PRPOpCode
from typing import Optional, Any


class TypeRawData(VisitableType):
    def __init__(self):
        super().__init__()

    def visit(self, current_instruction_index: int, instructions: [PRPInstruction], owner_typename: Optional[str]) -> (int, []):
        current_instruction: PRPInstruction = instructions[current_instruction_index]

        assert current_instruction.op_code == PRPOpCode.Container or \
               current_instruction.op_code == PRPOpCode.NamedContainer, "for ZRawData required Container or NamedContainer"

        if current_instruction.op_data['length'] > 0:
            next_instruction: PRPInstruction = instructions[current_instruction_index + 1]
            assert next_instruction.op_code == PRPOpCode.RawData or \
                next_instruction.op_code == PRPOpCode.NamedRawData, "for ZRawData next instruction must be raw data if container not empty"

            return current_instruction_index + 2, ['0x{:02X}'.format(x) for x in next_instruction.op_data['data']]

        return current_instruction_index + 1, []

    def to_prp(self, value: Any) -> [PRPInstruction]:
        length: int = len(value)
        result: [PRPInstruction] = [PRPInstruction(PRPOpCode.Container, {'length': length})]
        if length > 0:
            result.append(PRPInstruction(PRPOpCode.RawData, [bytes.fromhex(x[2:])[0] for x in value]))

        return result

    def check_value(self, value: Any) -> bool:
        return isinstance(value, list)

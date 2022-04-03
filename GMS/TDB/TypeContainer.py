from PRP import PRPInstruction, PRPOpCode
from GMS.TDB.VisitableType import VisitableType
from typing import Optional, Any


class TypeContainer(VisitableType):
    def __init__(self):
        pass

    def visit(self, current_instruction_index: int, instructions: [PRPInstruction], owner_typename: Optional[str]) -> (int, []):
        current_instruction: PRPInstruction = instructions[current_instruction_index]

        assert current_instruction.op_code == PRPOpCode.Container or \
               current_instruction.op_code == PRPOpCode.NamedContainer, \
               f"Expected Container or NamedContainer; got {str(current_instruction.op_code)}. " \
               f"Instruction index {current_instruction_index}"

        num_inner_objects: int = current_instruction.op_data['length']

        ret_container_obj: dict = dict()
        ret_container_obj['length'] = num_inner_objects
        ret_container_obj['data'] = []

        current_instruction_index += 1

        entry_idx: int
        for entry_idx in range(0, num_inner_objects):
            chld_obj: dict = dict()
            chld_obj['type'] = str(instructions[current_instruction_index].op_code)
            chld_obj['value'] = instructions[current_instruction_index].op_data
            ret_container_obj['data'].append(chld_obj)
            current_instruction_index += 1

        return current_instruction_index, ret_container_obj

    def to_prp(self, value: Any) -> [PRPInstruction]:
        length: int = value["length"]
        data = value["data"]
        result: [PRPInstruction] = [PRPInstruction(PRPOpCode.Container, {'length': length})]

        for data_ent in data:
            data_type: str = data_ent["type"]
            if data_type.startswith('PRPOpCode.'):
                result.append(PRPInstruction(PRPOpCode[data_type.split('.')[1]], data_ent['value']))
            else:
                breakpoint()

        return result

    def check_value(self, value: Any) -> bool:
        return "length" in value and "data" in value

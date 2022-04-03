from typing import Optional, Any
from PRP import PRPInstruction, PRPOpCode
from GMS.TDB.VisitableType import VisitableType


class TypeArray(VisitableType):
    def __init__(self, expected_length: Optional[int], entry_type: PRPOpCode, transform: dict):
        self._expected_length: Optional[int] = expected_length
        self._entry_type: PRPOpCode = entry_type
        self._transform: dict = transform

        if self.expected_length is not None:
            assert self.expected_length >= 0

    @property
    def expected_length(self) -> Optional[int]:
        return self._expected_length

    @property
    def inner_op_code(self) -> PRPOpCode:
        return self._entry_type

    @property
    def transform(self) -> dict:
        return self._transform

    def visit(self, current_instruction_index: int, instructions: [PRPInstruction], owner_typename: Optional[str]) -> (int, []):
        current_instruction: PRPInstruction = instructions[current_instruction_index]

        if current_instruction.op_code != PRPOpCode.Array and current_instruction.op_code != PRPOpCode.NamedArray:
            raise RuntimeError(f"Expected Array/NamedArray, got {str(current_instruction.op_code)}")

        if self._expected_length is not None and self._expected_length != current_instruction.op_data['length']:
            raise RuntimeError(
                f"Expected length of array {self._expected_length}, got {current_instruction.op_data['length']}")

        current_instruction_index += 1

        result: [] = []

        prepared_instructions: int = 0
        while instructions[current_instruction_index].op_code != PRPOpCode.EndArray or \
                (prepared_instructions < self._expected_length if self._expected_length is not None else False):
            # ----- Begin loop -----
            c_val: PRPInstruction = instructions[current_instruction_index]

            if c_val.op_code != self._entry_type:
                raise RuntimeError(f"Expected type {str(self._entry_type)}, got {str(c_val.op_code)}")

            result.append(c_val.op_data)
            current_instruction_index += 1
            prepared_instructions += 1

        # TODO: Add assertion here

        current_instruction = instructions[current_instruction_index]
        if current_instruction.op_code != PRPOpCode.EndArray:
            raise RuntimeError(
                f"Expected end of array, got {current_instruction.op_code} (idx = {current_instruction_index})")

        current_instruction_index += 1
        ret_array_obj: dict = dict()
        # if owner_typename is not None:
        #     ret_array_obj['owner'] = owner_typename

        ret_array_obj['array'] = dict()
        ret_array_obj['array']['length'] = len(result)
        ret_array_obj['array']['data'] = result
        ret_array_obj['array']['type'] = str(self._entry_type)

        return current_instruction_index, ret_array_obj

    def to_prp(self, value: Any) -> [PRPInstruction]:
        entries = value['array']['data']
        result: [PRPInstruction] = [PRPInstruction(PRPOpCode.Array, {'length': len(entries)})]
        for ent in entries:
            result.append(PRPInstruction(self._entry_type, ent))

        result.append(PRPInstruction(PRPOpCode.EndArray))
        return result

    def check_value(self, value: Any) -> bool:
        entries: int = value['array']['data']
        if self._expected_length is not None and len(entries) != self._expected_length:
            return False

        if PRPOpCode[value['array']['type'].split('.')[1]] != self._entry_type:
            return False

        return True

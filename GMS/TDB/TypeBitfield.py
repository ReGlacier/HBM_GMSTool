from GMS.TDB.VisitableType import VisitableType
from PRP import PRPInstruction, PRPOpCode
from typing import Optional, Any


class TypeBitfield(VisitableType):
    def __init__(self, self_typename: str, masks: dict, prp_type: PRPOpCode):
        self._masks: dict = masks
        self._prp_type: PRPOpCode = prp_type
        self._self_typename: str = self_typename

    @property
    def masks(self) -> dict:
        return self._masks

    def visit(self, current_instruction_index: int, instructions: [PRPInstruction], owner_typename: Optional[str]) -> (int, []):
        current_instruction: PRPInstruction = instructions[current_instruction_index]

        assert current_instruction.op_code == PRPOpCode.StringArray, \
            f"Expected string array, got {str(current_instruction.op_code)}" \
            f", instruction index {current_instruction_index}"

        result: int = 0
        used_masks: [str] = []

        str_entry: str
        for str_entry in current_instruction.op_data:
            if str_entry not in self._masks:
                raise RuntimeError(f"Entry {str_entry} not defined in self mask of type {self._self_typename}. Please, check type definition. Instruction index {current_instruction_index}")

            result |= self._masks[str_entry]
            used_masks.append(str_entry)

        ret_obj: dict = dict()
        if owner_typename is not None:
            ret_obj['owner'] = owner_typename

        ret_obj['type'] = self._self_typename
        ret_obj['value'] = dict()
        ret_obj['value']['integral'] = result
        ret_obj['value']['mask_list'] = used_masks

        return current_instruction_index + 1, [ret_obj]

    def to_prp(self, value: Any) -> [PRPInstruction]:
        result: [PRPInstruction] = []

        if isinstance(value, list):
            mask_refs: [str] = []
            for x in range(0, len(value)):
                for mask in value[x]['value']['mask_list']:
                    mask_refs.append(mask)

            result.append(PRPInstruction(PRPOpCode.StringArray, mask_refs))
            return result
        else:
            breakpoint()

    def check_value(self, value: Any) -> bool:
        if isinstance(value, list):
            for x in range(0, len(value)):
                for mask in value[x]['value']['mask_list']:
                    if mask not in self._masks:
                        return False

            return True
        else:
            breakpoint()

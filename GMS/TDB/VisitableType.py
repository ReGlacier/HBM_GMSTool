from typing import Optional, Any
from PRP import PRPInstruction


class VisitableType:
    def visit(self, current_instruction_index: int, instructions: [PRPInstruction], owner_typename: Optional[str]) -> (int, []):
        raise NotImplementedError("You must implement method 'visit' in your own class")

    def to_prp(self, value: Any) -> [PRPInstruction]:
        raise NotImplementedError("You must implement method 'to_prp' in your own class")

    def check_value(self, value: Any) -> bool:
        raise NotImplementedError("You must implement method 'check_value' in your own class")

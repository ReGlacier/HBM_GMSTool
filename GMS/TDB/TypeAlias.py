from typing import Optional, Union, Any
from PRP import PRPOpCode, PRPInstruction


from GMS.TDB.TypeLink import TypeLink
from GMS.TDB.TypeDataBase import TypeDataBase
from GMS.TDB.VisitableType import VisitableType



class TypeAlias(TypeLink, VisitableType):
    def __init__(self, self_name: str, final_type: str):
        from GMS.TDB.Type import Type

        super().__init__()

        self._self_name: str = self_name
        self._need_resolve_linking: bool = True
        self.final_type: Union[str, Type, PRPOpCode, None] = None

        if final_type.startswith('PRPOpCode.'):
            self.final_type = PRPOpCode[final_type.split('.')[1]]
            self._need_resolve_linking = False
        else:
            self.final_type = final_type

    def resolve_external_links(self, tdb: TypeDataBase):
        if not self._need_resolve_linking:
            return

        self.final_type = tdb.find_type(self.final_type)
        if self.final_type is not None:
            self._need_resolve_linking = False

    def visit(self, current_instruction_index: int, instructions: [PRPInstruction], owner_typename: Optional[str]) -> (int, []):
        if self._need_resolve_linking or self.final_type is None:
            return -1, []

        if type(self.final_type) is PRPOpCode:
            ret_obj: dict = dict()
            ret_obj['owner'] = self._self_name
            ret_obj['value'] = instructions[current_instruction_index].op_data
            ret_obj['type'] = instructions[current_instruction_index].op_code

            return current_instruction_index + 1, ret_obj
        else:
            from GMS.TDB.Type import Type

            ft: Type = self.final_type
            return ft.visit(current_instruction_index, instructions, owner_typename)

        return -1, []

    def to_prp(self, value: Any) -> [PRPInstruction]:
        if self.final_type is None:
            raise RuntimeError(f"Final type of alias {self._self_name} not resolved!")

        if type(self.final_type) is PRPOpCode:
            return [PRPInstruction(self.final_type, value['value'])]
        else:
            breakpoint()

    def check_value(self, value: Any) -> bool:
        if type(self.final_type) is PRPOpCode:
            return True
        else:
            breakpoint()



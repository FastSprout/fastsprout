from pathlib import Path

from tests.type_checking import TypeChecker


class TestTyping:
    def test_crud_typing_contract(self, type_checker: TypeChecker) -> None:
        # given
        source = Path(__file__).with_name("crud_typing.py.txt")
        # when / then
        type_checker.check(source)

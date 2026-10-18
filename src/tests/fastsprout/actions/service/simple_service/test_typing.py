from pathlib import Path

from tests.type_checking import TypeChecker


class TestServiceTyping:
    def test_contract(self, type_checker: TypeChecker) -> None:
        # given
        source = Path(__file__).with_name("service_typing.py.txt")

        # when / then
        type_checker.check(source)

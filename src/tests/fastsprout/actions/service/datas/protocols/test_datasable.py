from pathlib import Path

from tests.type_checking import TypeChecker


class TestDataSable:
    def test_typing_contract(self, type_checker: TypeChecker) -> None:
        # given
        source = Path(__file__).with_name("datasable_typing.py.txt")

        # then
        type_checker.check(source)

from pathlib import Path

from tests.type_checking import TypeChecker


def test_dto_typing_contract(type_checker: TypeChecker) -> None:
    type_checker.check(Path(__file__).with_name("dto_typing.py.txt"))

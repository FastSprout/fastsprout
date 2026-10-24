from pathlib import Path

from tests.type_checking import TypeChecker


def test_dataclass_typing(type_checker: TypeChecker) -> None:
    type_checker.check(Path(__file__).with_name("dataclass_typing.py.txt"))

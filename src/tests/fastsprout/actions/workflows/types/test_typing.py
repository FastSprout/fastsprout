from pathlib import Path

from tests.type_checking import TypeChecker


def test_workflow_typing_contract(type_checker: TypeChecker) -> None:
    type_checker.check(Path(__file__).with_name("workflow_typing.py.txt"))

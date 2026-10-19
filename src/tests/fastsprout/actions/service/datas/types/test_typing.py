from pathlib import Path

from fastsprout.testing.core import when_then
from tests.type_checking import TypeChecker


@when_then("crud typing contract")
def test_crud_typing_contract(type_checker: TypeChecker) -> None:
    type_checker.check(Path(__file__).with_name("query_typing.py.txt"))
    type_checker.check(Path(__file__).with_name("crud_typing.py.txt"))


@when_then("datasable typing contract")
def test_datasable_typing_contract(type_checker: TypeChecker) -> None:
    type_checker.check(Path(__file__).with_name("datasable_typing.py.txt"))

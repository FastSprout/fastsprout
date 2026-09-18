from pathlib import Path

from tests.type_checking import TypeChecker


def test_sql_entity_typing_contract(type_checker: TypeChecker) -> None:
    type_checker.check(Path(__file__).with_name("entity_typing.py.txt"))

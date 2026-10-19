from pathlib import Path

import pytest

from tests.type_checking import TypeChecker


@pytest.mark.parametrize(
    "case",
    ["entity_typing.py.txt", "query_typing.py.txt", "query_for_typing.py.txt"],
)
def test_sql_entity_typing_contract(
    type_checker: TypeChecker, case: str
) -> None:
    type_checker.check(Path(__file__).with_name(case))

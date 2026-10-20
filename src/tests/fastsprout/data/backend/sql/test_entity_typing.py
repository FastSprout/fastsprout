from pathlib import Path
from subprocess import CompletedProcess

import pytest

from fastsprout.testing.core import then, when
from tests.type_checking import TypeChecker


@when("SQL entity and query clients are checked")
def checked_types(
    type_checker: TypeChecker, case: str
) -> CompletedProcess[str]:
    return type_checker.run(Path(__file__).with_name(case))


@pytest.mark.parametrize(
    "case",
    [
        "entity_typing.py.txt",
        "query_typing.py.txt",
        "query_for_typing.py.txt",
        "source_typing.py.txt",
    ],
)
@then("SQL entity and query contracts preserve their declared types")
def test_sql_entity_typing_contract(
    type_checker: TypeChecker,
    case: str,
    checked_types: CompletedProcess[str],
) -> None:
    type_checker.verify(Path(__file__).with_name(case), checked_types)

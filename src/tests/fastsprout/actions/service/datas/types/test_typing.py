from pathlib import Path
from subprocess import CompletedProcess

from fastsprout.testing.core import then, when
from tests.type_checking import TypeChecker


@when("CRUD and query type clients are checked")
def checked_crud(
    type_checker: TypeChecker,
) -> tuple[CompletedProcess[str], CompletedProcess[str]]:
    return type_checker.run(
        Path(__file__).with_name("query_typing.py.txt")
    ), type_checker.run(Path(__file__).with_name("crud_typing.py.txt"))


@then("crud typing contract")
def test_crud_typing_contract(
    type_checker: TypeChecker,
    checked_crud: tuple[CompletedProcess[str], CompletedProcess[str]],
) -> None:
    query, crud = checked_crud
    type_checker.verify(Path(__file__).with_name("query_typing.py.txt"), query)
    type_checker.verify(Path(__file__).with_name("crud_typing.py.txt"), crud)


@when("the DataS protocol client is checked")
def checked_protocol(type_checker: TypeChecker) -> CompletedProcess[str]:
    return type_checker.run(Path(__file__).with_name("datasable_typing.py.txt"))


@then("datasable typing contract")
def test_datasable_typing_contract(
    type_checker: TypeChecker, checked_protocol: CompletedProcess[str]
) -> None:
    type_checker.verify(
        Path(__file__).with_name("datasable_typing.py.txt"), checked_protocol
    )

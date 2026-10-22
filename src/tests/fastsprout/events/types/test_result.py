from pathlib import Path
from subprocess import CompletedProcess

from fastsprout.testing.core import then, when
from tests.type_checking import TypeChecker


@when("the schema-routed event result client is type checked")
def checked_result(type_checker: TypeChecker) -> CompletedProcess[str]:
    return type_checker.run(Path(__file__).with_name("result_typing.py.txt"))


@then("raw and schema-routed results retain their declared types")
def test_result_typing(
    type_checker: TypeChecker, checked_result: CompletedProcess[str]
) -> None:
    type_checker.verify(
        Path(__file__).with_name("result_typing.py.txt"), checked_result
    )

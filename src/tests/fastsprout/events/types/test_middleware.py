from pathlib import Path
from subprocess import CompletedProcess

from fastsprout.testing.core import then, when
from tests.type_checking import TypeChecker


@when("the middleware client is type checked")
def checked_middleware(type_checker: TypeChecker) -> CompletedProcess[str]:
    return type_checker.run(
        Path(__file__).with_name("middleware_typing.py.txt")
    )


@then("middleware preserves constructor arguments and its event type")
def test_middleware_typing(
    type_checker: TypeChecker, checked_middleware: CompletedProcess[str]
) -> None:
    type_checker.verify(
        Path(__file__).with_name("middleware_typing.py.txt"), checked_middleware
    )

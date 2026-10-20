from pathlib import Path
from subprocess import CompletedProcess

from fastsprout.testing.core import then, when
from tests.type_checking import TypeChecker


@when("the broker context client is checked")
def checked_brokers(type_checker: TypeChecker) -> CompletedProcess[str]:
    return type_checker.run(Path(__file__).with_name("brokers_typing.py.txt"))


@then("testing contexts preserve their concrete broker types and protocol")
def test_broker_types(
    type_checker: TypeChecker, checked_brokers: CompletedProcess[str]
) -> None:
    type_checker.verify(
        Path(__file__).with_name("brokers_typing.py.txt"), checked_brokers
    )

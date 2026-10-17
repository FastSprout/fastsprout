from pathlib import Path

from tests.type_checking import TypeChecker


def test_flat_join_tuple_typing(type_checker: TypeChecker) -> None:
    type_checker.check(Path(__file__).with_name("join_typing.py.txt"))


def test_bulk_create_iterable_typing(type_checker: TypeChecker) -> None:
    type_checker.check(Path(__file__).with_name("bulk_typing.py.txt"))

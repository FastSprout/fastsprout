"""Validate typed fixtures and test arguments through public pytest hooks."""

from collections.abc import Generator, Sequence
from inspect import (
    getsourcefile,
    isasyncgenfunction,
    iscoroutinefunction,
    isgeneratorfunction,
    unwrap,
)
from pathlib import Path
from types import MethodType
from typing import Protocol, runtime_checkable

import pytest
from hypothesis import is_hypothesis_test
from typeguard import TypeCheckError

from fastsprout.core.types.protocols.ables import Hashable

from .contracts import (
    FIXTURE_CONTRACTS,
    check_arguments,
    check_result,
    checked,
    checked_async,
    checked_signature,
)

__all__ = [
    "pytest_collection_modifyitems",
    "pytest_configure",
    "pytest_fixture_setup",
    "pytest_runtest_call",
]


class FixtureDefinition(Protocol):
    @property
    def func(self) -> Hashable: ...

    @property
    def argnames(self) -> tuple[str, ...]: ...


@runtime_checkable
class FixtureResolver(Protocol):
    def getfixturedefs(
        self, argname: str, node: pytest.Item
    ) -> Sequence[FixtureDefinition] | None: ...


TYPED_FIXTURES: pytest.StashKey[set[Hashable]] = pytest.StashKey()


def fixture_identity(function: Hashable) -> Hashable:
    if callable(function):
        function = unwrap(function)
    return function.__func__ if isinstance(function, MethodType) else function


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "fastsprout_typed: Require typed providers and test parameters.",
    )


def fixture_names(item: pytest.Function) -> set[str]:
    parameters: set[str] = set()
    for marker in item.iter_markers("parametrize"):
        indirect = marker.kwargs.get("indirect", False)
        if indirect is True:
            continue
        names = marker.args[0]
        names = (
            names.replace(" ", "").split(",")
            if isinstance(names, str)
            else names
        )
        parameters.update(set(names) - set(indirect or ()))
    return set(item.fixturenames) - parameters


def register_fixtures(item: pytest.Function) -> None:
    resolver = item.config.pluginmanager.get_plugin("funcmanage")
    if not isinstance(resolver, FixtureResolver):
        raise pytest.UsageError("Pytest fixture resolver is unavailable")
    fixtures = item.config.stash.setdefault(TYPED_FIXTURES, set())
    for name in fixture_names(item):
        for definition in reversed(resolver.getfixturedefs(name, item) or ()):
            fixtures.add(fixture_identity(definition.func))
            if name not in definition.argnames:
                break


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    for item in items:
        if isinstance(item, pytest.Function) and item.get_closest_marker(
            "fastsprout_typed"
        ):
            register_fixtures(item)
        if isinstance(item, pytest.Function) and is_hypothesis_test(item.obj):
            try:
                inner = item.obj.hypothesis.inner_test
                item.obj.hypothesis.inner_test = (
                    checked_async(inner)
                    if iscoroutinefunction(inner)
                    else checked(inner)
                )
            except TypeError as error:
                raise pytest.UsageError(str(error)) from error


@pytest.hookimpl(wrapper=True)
def pytest_fixture_setup[T](
    fixturedef: pytest.FixtureDef[T], request: pytest.FixtureRequest
) -> Generator[None, T, T]:
    function = unwrap(fixturedef.func)
    if isinstance(function, MethodType):
        function = function.__func__
    contract = FIXTURE_CONTRACTS.get(function)
    source = getsourcefile(function)
    if (
        contract is None
        and function in request.config.stash.get(TYPED_FIXTURES, set())
        and source
        and Path(source).is_relative_to(request.config.rootpath)
        and not Path(source).is_relative_to(Path(pytest.__file__).parent.parent)
    ):
        contract = checked_signature(function)
    if contract is None:
        return (yield)
    check_arguments(
        contract.bind_partial(
            **{
                name: request.getfixturevalue(name)
                for name in fixturedef.argnames
            }
        )
    )
    result = yield
    try:
        return check_result(
            result,
            contract,
            yielded=isgeneratorfunction(function)
            or isasyncgenfunction(function),
        )
    except TypeCheckError:
        fixturedef.cached_result = None
        raise


def pytest_runtest_call(item: pytest.Item) -> None:
    if not isinstance(item, pytest.Function) or not item.get_closest_marker(
        "fastsprout_typed"
    ):
        return
    contract = checked_signature(item.obj)
    check_arguments(
        contract.bind_partial(
            **{
                name: item.funcargs[name]
                for name in contract.parameters
                if name in item.funcargs
            }
        )
    )

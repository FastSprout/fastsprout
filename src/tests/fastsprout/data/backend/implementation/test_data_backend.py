from inspect import isabstract

import pytest

from fastsprout.data.backend.implementation import BaseDataBackend
from fastsprout.data.backend.protocols import Finalizable
from fastsprout.data.backend.sql.data_backend import SQLDataBackend
from fastsprout.testing.core import given, then, when


class IncompleteBackend(BaseDataBackend[None, Finalizable]): ...


class TestAbstractBackend:
    @given("a complete SQL backend or an incomplete backend declaration")
    def backend(
        self, complete: bool
    ) -> type[SQLDataBackend] | type[IncompleteBackend]:
        return SQLDataBackend if complete else IncompleteBackend

    @when("Python determines whether the backend can be instantiated")
    def abstract(
        self, backend: type[SQLDataBackend] | type[IncompleteBackend]
    ) -> bool:
        return isabstract(backend)

    @pytest.mark.parametrize("complete", [False, True])
    @then("only a backend implementing its binding contract is concrete")
    def test_binding_contract(self, abstract: bool, complete: bool) -> None:
        assert abstract is not complete

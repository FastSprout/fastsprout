import subprocess
import sys

import pytest

from fastsprout.testing.core import given, then, when


class TestOptionalSQLDependencies:
    @given("an interpreter with a failed transitive SQL dependency")
    def client(self) -> str:
        return """
import sys
from collections.abc import Sequence
from importlib.abc import MetaPathFinder
from importlib.machinery import ModuleSpec
from types import ModuleType

class MissingDependency(MetaPathFinder):
    def find_spec(
        self,
        fullname: str,
        path: Sequence[str] | None = None,
        target: ModuleType | None = None,
    ) -> ModuleSpec | None:
        if fullname == sys.argv[1]:
            raise ModuleNotFoundError(
                'A transitive dependency is missing',
                name='missing_transitive_dependency',
            )
        return None

sys.meta_path.insert(0, MissingDependency())
try:
    import fastsprout.data
except ModuleNotFoundError as error:
    print(error.name)
else:
    raise AssertionError('Unexpected dependency errors must propagate')
"""

    @when("DataR or the relationship integration imports that dependency")
    def imported(
        self, client: str, module: str
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-c", client, module],
            capture_output=True,
            text=True,
            check=False,
            timeout=15,
        )

    @pytest.mark.parametrize(
        "module",
        ["fastsprout.data.backend.sql", "fastsprout.data.relationship"],
    )
    @then("only explicitly optional dependencies may be suppressed")
    def test_transitive_import_failure(
        self, imported: subprocess.CompletedProcess[str]
    ) -> None:
        assert imported.returncode == 0, imported.stderr
        assert imported.stdout.strip() == "missing_transitive_dependency"

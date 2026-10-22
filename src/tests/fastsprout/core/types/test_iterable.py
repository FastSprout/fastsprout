import subprocess
import sys

from fastsprout.testing.core import given, then, when


class TestUntypedIterable:
    @given("a scalar passed to iterable resolution by an untyped caller")
    def client(self) -> str:
        return """
import asyncio
from fastsprout.core.types.iterable import resolve_any_iterable

asyncio.run(anext(resolve_any_iterable(1)))
"""

    @when("iteration starts")
    def rejected(self, client: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-c", client],
            capture_output=True,
            text=True,
            check=False,
            timeout=15,
        )

    @then("the scalar is rejected with an explicit iterable contract error")
    def test_scalar(self, rejected: subprocess.CompletedProcess[str]) -> None:
        assert rejected.returncode != 0
        assert (
            "TypeError: Expected an iterable or async iterable"
            in rejected.stderr
        )

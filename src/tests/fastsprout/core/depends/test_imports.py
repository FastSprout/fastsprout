import subprocess
import sys

from fastsprout.testing.core import given, then, when


class TestOptionalFastAPI:
    @given("a fresh interpreter where FastAPI cannot be imported")
    def client(self) -> str:
        return """
import asyncio
import sys
from functools import partial
from importlib.abc import MetaPathFinder

class WithoutFastAPI(MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.partition('.')[0] == 'fastapi':
            raise ModuleNotFoundError('FastAPI is not installed', name='fastapi')

sys.meta_path.insert(0, WithoutFastAPI())

from fastsprout.core import Depends, inject_depends

def provider() -> int:
    return 42

@inject_depends
def sync(value: int = Depends(provider)) -> int:
    return value

@inject_depends
async def asynchronous(value: int = Depends(provider)) -> int:
    return value

print(sync(), asyncio.run(asynchronous()))
print(repr(Depends(provider, use_cache=False)))
print(repr(Depends()))
print(repr(Depends(partial(provider))))
"""

    @when("sync and async dependencies use the fallback marker")
    def checked(self, client: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-c", client],
            text=True,
            capture_output=True,
            check=False,
            timeout=15,
        )

    @then(
        "dependency injection and marker representations do not require FastAPI"
    )
    def test_without_fastapi(
        self, checked: subprocess.CompletedProcess[str]
    ) -> None:
        assert checked.returncode == 0, checked.stdout + checked.stderr
        assert checked.stdout.splitlines() == [
            "42 42",
            "DependsClass(provider, use_cache=False)",
            "DependsClass(NoneType)",
            "DependsClass(partial)",
        ]

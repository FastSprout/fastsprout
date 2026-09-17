import sys
from pathlib import Path

import pytest

from tests.type_checking import TypeChecker


@pytest.fixture(scope="session")
def checker_python_version() -> str:
    """Match checker targets to the interpreter selected by the CI matrix."""
    return f"{sys.version_info.major}.{sys.version_info.minor}"


@pytest.fixture(params=["mypy", "basedpyright"])
def type_checker(
    request: pytest.FixtureRequest,
    tmp_path: Path,
    checker_python_version: str,
) -> TypeChecker:
    return TypeChecker(request.param, tmp_path, checker_python_version)

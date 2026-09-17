import sys

import pytest


@pytest.fixture(scope="session")
def checker_python_version() -> str:
    """Match checker targets to the interpreter selected by the CI matrix."""
    return f"{sys.version_info.major}.{sys.version_info.minor}"

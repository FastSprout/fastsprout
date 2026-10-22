import json
import re
import subprocess
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[5]

MYPY_CONFIG = "[mypy]\n"
MYPY_REVEAL = re.compile(r'Revealed type is "(?P<type>.+)"')
PYRIGHT_REVEAL = re.compile(r'^Type of "(?P<expr>.+)" is "(?P<type>.+)"$')


def write_tmp(code: str, suffix: str) -> Path:
    f = tempfile.NamedTemporaryFile(
        mode="w", suffix=suffix, delete=False, dir="/tmp"
    )
    f.write(code)
    f.close()
    return Path(f.name)


def run_mypy(code: str, python_version: str) -> list[str]:
    code_path = write_tmp(code, ".py")
    cfg_path = write_tmp(MYPY_CONFIG, ".ini")
    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "mypy",
                "--config-file",
                str(cfg_path),
                "--python-version",
                python_version,
                "--no-incremental",
                str(code_path),
            ],
            check=False,
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
    finally:
        code_path.unlink()
        cfg_path.unlink()
    return [
        m.group("type")
        for line in result.stdout.splitlines()
        if (m := MYPY_REVEAL.search(line))
    ]


def run_pyright(code: str, python_version: str) -> list[str]:
    code_path = write_tmp(code, ".py")
    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "basedpyright",
                "--outputjson",
                "--pythonversion",
                python_version,
                "--pythonpath",
                sys.executable,
                str(code_path),
            ],
            check=False,
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
    finally:
        code_path.unlink()
    payload = json.loads(result.stdout)
    return [
        m.group("type")
        for diag in payload.get("generalDiagnostics", [])
        if (m := PYRIGHT_REVEAL.match(diag["message"]))
    ]


RUNNERS: dict[str, Callable[[str, str], list[str]]] = {
    "mypy": run_mypy,
    "pyright": run_pyright,
}


@pytest.fixture
def reveal_types(
    checker_python_version: str,
) -> Callable[[str, str], list[str]]:
    """Return revealed types from `reveal_type(...)` calls in `code`.

    Usage: reveal_types("mypy", code) or reveal_types("pyright", code).
    """

    def reveal(tool: str, code: str) -> list[str]:
        return RUNNERS[tool](code, checker_python_version)

    return reveal

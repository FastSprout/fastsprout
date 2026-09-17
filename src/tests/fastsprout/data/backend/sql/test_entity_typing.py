import json
import subprocess
import sys
from pathlib import Path

import pytest

_CODE = """from typing import assert_type
from sqlmodel import Field as SQLField
from fastsprout.core import Field
from fastsprout.data.backend.sql import SQLEntity

class SQLUser(SQLEntity[int]):
    id: Field[int] = SQLField(primary_key=True)
    name: Field[str]

SQLUser(id=1, name="a")
SQLUser(1, "a")

def entities[T](source: type[T] | list[T]) -> list[T]:
    return []

assert_type(entities(SQLUser), list[SQLUser])
"""


@pytest.mark.parametrize(
    "checker,rule",
    [("mypy", "call-arg"), ("basedpyright", "reportCallIssue")],
)
def test_sql_entity_typing_contract(
    tmp_path: Path, checker: str, rule: str, checker_python_version: str
) -> None:
    case = tmp_path / "case.py"
    case.write_text(_CODE)
    if checker == "mypy":
        config = tmp_path / "mypy.ini"
        config.write_text(
            f"[mypy]\npython_version = {checker_python_version}\n"
        )
        args = [
            "--config-file",
            str(config),
            "--cache-dir",
            str(tmp_path / ".mypy_cache"),
            "--output=json",
            str(case),
        ]
    else:
        config = tmp_path / "pyrightconfig.json"
        config.write_text(
            json.dumps(
                {
                    "typeCheckingMode": "standard",
                    "pythonVersion": checker_python_version,
                    "include": [case.name],
                }
            )
        )
        args = [
            "--project",
            str(config),
            "--pythonpath",
            sys.executable,
            "--outputjson",
        ]
    result = subprocess.run(
        [sys.executable, "-m", checker, *args],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1, result.stdout + result.stderr
    if checker == "mypy":
        diagnostics = [json.loads(line) for line in result.stdout.splitlines()]
        actual = [
            (item["line"], item["code"])
            for item in diagnostics
            if item["severity"] == "error"
        ]
    else:
        diagnostics = json.loads(result.stdout)["generalDiagnostics"]
        actual = [
            (item["range"]["start"]["line"] + 1, item.get("rule"))
            for item in diagnostics
            if item["severity"] == "error"
        ]
    assert actual == [(11, rule)], diagnostics

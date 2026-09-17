import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest


@pytest.fixture
def dto_case(tmp_path: Path) -> Path:
    source = Path(__file__).with_name("dto_typing.py.txt").read_text()
    case = tmp_path / "client.py"
    case.write_text(source)
    return case


def _expected_errors(case: Path, marker: str) -> Counter[tuple[int, str]]:
    return Counter(
        (line_number, code.strip())
        for line_number, line in enumerate(case.read_text().splitlines(), 1)
        if marker in line
        for code in line.partition(marker)[2].split(";")[0].split(",")
    )


def test_stock_checker_dto_contract(tmp_path: Path, dto_case: Path) -> None:
    config = tmp_path / "pyrightconfig.json"
    config.write_text(
        json.dumps(
            {
                "typeCheckingMode": "standard",
                "pythonVersion": "3.12",
                "include": [dto_case.name],
            }
        )
    )
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "basedpyright",
            "--outputjson",
            "--pythonpath",
            sys.executable,
            "--project",
            str(config),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode in (0, 1), result.stdout + result.stderr
    diagnostics = json.loads(result.stdout)["generalDiagnostics"]
    actual = Counter(
        (item["range"]["start"]["line"] + 1, item.get("rule"))
        for item in diagnostics
        if item["severity"] == "error"
    )
    assert actual == _expected_errors(dto_case, "# error: "), diagnostics


def test_mypy_dto_contract(tmp_path: Path, dto_case: Path) -> None:
    config = tmp_path / "mypy.ini"
    config.write_text("[mypy]\npython_version = 3.12\n")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "mypy",
            "--config-file",
            str(config),
            "--cache-dir",
            str(tmp_path / ".mypy_cache"),
            "--output=json",
            str(dto_case),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode in (0, 1), result.stdout + result.stderr
    diagnostics = [json.loads(line) for line in result.stdout.splitlines()]
    errors = [item for item in diagnostics if item["severity"] == "error"]
    assert all(Path(item["file"]) == dto_case for item in errors), diagnostics
    actual = Counter((item["line"], item["code"]) for item in errors)
    assert actual == _expected_errors(dto_case, "; mypy: "), diagnostics

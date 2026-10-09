import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    "example",
    [
        pytest.param(example, id=example.relative_to(ROOT).as_posix())
        for example in sorted((ROOT / "examples").rglob("*.py"))
        if example.read_text(encoding="utf-8").strip()
    ],
)
def test_example_runs(example: Path) -> None:
    result = subprocess.run(
        [sys.executable, str(example)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.strip(), "Example did not print a result"

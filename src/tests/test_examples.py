from pathlib import Path

import pytest

from scripts.docs_nav import run_python_example

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    "example",
    [
        pytest.param(example, id=example.relative_to(ROOT).as_posix())
        for example in sorted((ROOT / "examples").rglob("*.py"))
        if example.name != "__init__.py"
        and example.read_text(encoding="utf-8").strip()
    ],
)
def test_example_runs(example: Path) -> None:
    assert run_python_example(example, ROOT).strip()

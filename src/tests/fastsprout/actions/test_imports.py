import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[4]
EXAMPLES = sorted((ROOT / "examples/actions/01_action").rglob("*.py"))

WITHOUT_SQL = """
import runpy
import sys
from importlib.abc import MetaPathFinder

class WithoutSQL(MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        package = fullname.partition(".")[0]
        if package in {"sqlalchemy", "sqlmodel"}:
            raise ModuleNotFoundError(f"No module named '{package}'", name=package)

sys.meta_path.insert(0, WithoutSQL())
runpy.run_path(sys.argv[1], run_name="__main__")
"""


@pytest.mark.parametrize("example", EXAMPLES, ids=lambda path: path.stem)
def test_action_example_does_not_require_sql(example: Path) -> None:
    result = subprocess.run(
        [sys.executable, "-c", WITHOUT_SQL, str(example)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout

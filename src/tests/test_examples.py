from pathlib import Path

import pytest

from fastsprout.testing.core import given, then, when
from scripts.docs_nav import run_python_example

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    "relative_source",
    [
        pytest.param(
            example.relative_to(ROOT), id=example.relative_to(ROOT).as_posix()
        )
        for example in [
            *(
                path
                for path in sorted((ROOT / "examples").rglob("*.py"))
                if path.stem.partition("_")[0].isdigit()
                and path.read_text(encoding="utf-8").strip()
            ),
            *(
                path
                for path in sorted((ROOT / "docs_src").rglob("*.py"))
                if 'if __name__ == "__main__":'
                in path.read_text(encoding="utf-8")
            ),
        ]
    ],
)
class TestRunnableExamples:
    @given("a runnable example in the repository")
    def example(self, relative_source: Path) -> Path:
        return ROOT / relative_source

    @when("the documentation runner executes the example")
    def output(self, example: Path) -> str:
        return run_python_example(example, ROOT)

    @then("the example finishes successfully and produces output")
    def test_output(self, output: str) -> None:
        assert output.strip()

from pathlib import Path

import pytest
from pylint.lint import Run
from pylint.reporters import CollectingReporter

import tools.pylint.names as names
from fastsprout.testing.core import when_then

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def lint(path: Path) -> list[tuple[str, int]]:
    reporter = CollectingReporter()
    Run(
        [
            "--rcfile",
            str(PROJECT_ROOT / "pyproject.toml"),
            "--persistent=n",
            str(path),
        ],
        reporter=reporter,
        exit=False,
    )
    return [(message.symbol, message.line) for message in reporter.messages]


@pytest.fixture
def package(tmp_path: Path) -> Path:
    (tmp_path / "__init__.py").write_text("__all__ = []\n")
    return tmp_path


@pytest.mark.parametrize(
    "code",
    [
        "class _Hidden: pass",
        "class __Hidden: pass",
        "class _: pass",
        "_LIMIT = 10",
        "_value = 1",
        "__value = 1",
        "__ = 1",
        "def function(_value): pass",
        "def _function(): pass",
        "async def _function(): pass",
        "class Visible:\n    _value = 1",
        "class Visible:\n    def __init__(self):\n        self._value = 1",
        "from pathlib import Path as _Path",
        "import pathlib as _pathlib",
    ],
)
def test_private_names_are_rejected(package: Path, code: str) -> None:
    path = package / "names_case.py"
    path.write_text(code + "\n")
    assert [symbol for symbol, _ in lint(path)] == ["private-name"]


def test_public_names_discard_and_magic_methods_are_allowed(
    package: Path,
) -> None:
    path = package / "public_case.py"
    path.write_text(
        "__all__ = ['Visible']\n"
        "LIMIT = 10\n"
        "class Visible:\n"
        "    def __init__(self): self.value = 1\n"
        "    def __call__(self, _): return self.value\n"
        "    def __iter__(self): yield self.value\n"
        "    async def __aenter__(self): return self\n"
        "_, value = (1, 2)\n"
    )
    assert lint(path) == []


@pytest.mark.parametrize(
    "filename", ["_module.py", "__module.py", "__main__.py"]
)
def test_private_filenames_are_rejected(package: Path, filename: str) -> None:
    path = package / filename
    path.write_text("value = 1\n")
    assert lint(path) == [("private-module-name", 1)]


def test_init_filename_is_allowed(package: Path) -> None:
    assert lint(package / "__init__.py") == []


def test_package_init_is_required(tmp_path: Path) -> None:
    path = tmp_path / "module.py"
    path.write_text("value = 1\n")
    assert lint(path) == [("missing-package-init", 1)]
    (tmp_path / "__init__.py").write_text("__all__ = []\n")
    assert lint(path) == []


def test_repository_root_does_not_require_init(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(names, "PROJECT_ROOT", tmp_path)
    path = tmp_path / "module.py"
    path.write_text("value = 1\n")
    assert lint(path) == []


@pytest.mark.parametrize("relative", [False, True])
@pytest.mark.parametrize(
    "exports",
    [
        "['Public']",
        "('Public',)",
        "[]",
        "[]\n__all__.append('Public')",
        "[]\n__all__.extend(['Public'])",
        "[]\n__all__ += ['Public']",
        "[]\nif True:\n    __all__.append('Public')",
    ],
)
def test_imports_respect_all(
    package: Path, monkeypatch: pytest.MonkeyPatch, relative: bool, exports: str
) -> None:
    monkeypatch.syspath_prepend(str(package.parent))
    (package / "provider.py").write_text(
        f"__all__ = {exports}\nPublic = 1\nHidden = 2\n"
    )
    path = package / "consumer.py"
    source = ".provider" if relative else f"{package.name}.provider"
    path.write_text(
        f"from {source} import Public\n"
        f"from {source} import Hidden as Alias\n"
        f"from {source} import *\n"
    )
    expected = [("import-outside-all", 2)]
    if exports == "[]":
        expected.insert(0, ("import-outside-all", 1))
    assert lint(path) == expected


def test_imports_without_all_or_unavailable_source_do_not_crash(
    package: Path,
) -> None:
    path = package / "imports_case.py"
    path.write_text(
        "from math import sqrt\n"
        "from unavailable_fastsprout_test_module import Missing\n"
    )
    assert lint(path) == []


def test_public_alias_cannot_hide_import_outside_all(package: Path) -> None:
    path = package / "alias_case.py"
    path.write_text("from typing import _ProtocolMeta as ProtocolMeta\n")
    assert lint(path) == [("import-outside-all", 1)]


class TestTestingPhases:
    @when_then("BDD declarations follow their phase and typing contracts")
    @pytest.mark.parametrize(
        "declaration, expected",
        [
            ("@given('context')\ndef context() -> int: return 1", []),
            (
                "@when('change')\nasync def changed(value: int) -> int: return value",
                [],
            ),
            (
                "@then('result')\ndef test_value(value: int) -> None: assert value == 1",
                [],
            ),
            (
                "class Cases:\n    @given('context')\n    def context(self) -> int: return 1",
                [],
            ),
            (
                "@given('context')\n@when('change')\ndef context() -> int: return 1",
                [("conflicting-test-phases", 4)],
            ),
            (
                "@given('context')\ndef context(): return 1",
                [("untyped-test-phase", 3)],
            ),
            (
                "@when('change')\ndef changed(value, /, *, count: int) -> int: return count",
                [("untyped-test-phase", 3)],
            ),
            (
                "@then('result')\ndef test_value(*items, **extras) -> None: pass",
                [("untyped-test-phase", 3), ("untyped-test-phase", 3)],
            ),
            (
                "@given('context')\ndef context() -> int:\n    # given\n    return 1",
                [("redundant-test-phase-comment", 4)],
            ),
            (
                "@when_then('result')\nasync def test_value() -> None:\n    # when / then\n    pass",
                [("redundant-test-phase-comment", 4)],
            ),
            (
                "@given('context')\ndef context() -> str:\n    return '''\n    # given\n    '''",
                [],
            ),
            (
                "from fastsprout.testing.core import given as arrange\n@arrange('context')\ndef context(): return 1",
                [("untyped-test-phase", 4)],
            ),
            (
                "import fastsprout.testing.core as testing\n@testing.then('result')\ndef test_value(): pass",
                [("untyped-test-phase", 4)],
            ),
            (
                "from hypothesis import given\n@given()\ndef test_value():\n    # given\n    pass",
                [],
            ),
            (
                "def given(value): return value\n@given\ndef test_value():\n    # given\n    pass",
                [],
            ),
        ],
    )
    def test_declarations(
        self, package: Path, declaration: str, expected: list[tuple[str, int]]
    ) -> None:
        path = package / "phases_case.py"
        path.write_text(
            "from fastsprout.testing.core import given, when, then, when_then\n"
            + declaration
            + "\n"
        )
        assert lint(path) == expected

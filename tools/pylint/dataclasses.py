"""Require the FastSprout dataclass decorator."""

from pathlib import Path

import astroid.nodes as nodes
from pylint.checkers import BaseChecker
from pylint.lint import PyLinter

__all__ = ["DataclassChecker", "register"]

IMPLEMENTATION = (
    Path(__file__).resolve().parents[2]
    / "src/fastsprout/core/decorators/dataclasses/dataclass.py"
)


class DataclassChecker(BaseChecker):
    name = "fastsprout-dataclass"

    def __init__(self, linter: PyLinter) -> None:
        super().__init__(linter)
        self.msgs = {
            "C9502": (
                "Use fastsprout.core.dataclass instead of the stdlib decorator",
                "stdlib-dataclass",
                "Only the FastSprout dataclass implementation may import the stdlib decorator.",
            ),
        }

    def check(self, node: nodes.Import | nodes.ImportFrom) -> None:
        module = node.root()
        if module.file and Path(module.file).resolve() == IMPLEMENTATION:
            return
        self.add_message("stdlib-dataclass", node=node)

    def visit_import(self, node: nodes.Import) -> None:
        if any(name == "dataclasses" for name, _ in node.names):
            self.check(node)

    def visit_importfrom(self, node: nodes.ImportFrom) -> None:
        if (
            not node.level
            and node.modname == "dataclasses"
            and any(name in {"dataclass", "*"} for name, _ in node.names)
        ):
            self.check(node)


def register(linter: PyLinter) -> None:
    linter.register_checker(DataclassChecker(linter))

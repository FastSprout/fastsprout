"""Require explicit exports in every FastSprout library module."""

from pathlib import Path

from astroid import nodes
from pylint.checkers import BaseChecker
from pylint.lint import PyLinter

__all__ = ["ModuleExportsChecker", "register"]

_LIBRARY_ROOT = Path(__file__).resolve().parents[2] / "src" / "fastsprout"


class ModuleExportsChecker(BaseChecker):
    name = "module-exports"

    def __init__(self, linter: PyLinter) -> None:
        super().__init__(linter)
        self.msgs = {
            "C9501": (
                "Library module must define __all__",
                "missing-module-all",
                "Declare the public exports, including an empty list for modules without exports.",
            ),
        }

    def visit_module(self, node: nodes.Module) -> None:
        if node.file is None or not Path(node.file).resolve().is_relative_to(
            _LIBRARY_ROOT
        ):
            return
        if not any(
            isinstance(binding.parent, (nodes.Assign, nodes.AnnAssign))
            and binding.parent.value is not None
            and binding.scope() is node
            for binding in node.locals.get("__all__", ())
        ):
            self.add_message("missing-module-all", node=node, line=1)


def register(linter: PyLinter) -> None:
    linter.register_checker(ModuleExportsChecker(linter))

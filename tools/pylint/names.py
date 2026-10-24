"""Reject private names and require explicit Python packages."""

from pathlib import Path

import astroid.nodes as nodes
from pylint.checkers import BaseChecker
from pylint.lint import PyLinter

__all__ = ["NamesChecker", "register"]

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class NamesChecker(BaseChecker):
    name = "fastsprout-names"

    def __init__(self, linter: PyLinter) -> None:
        super().__init__(linter)
        self.msgs = {
            "C9504": (
                "%s name %r must not start with an underscore",
                "private-name",
                "Use public names; discard variables and Python dunders are allowed.",
            ),
            "C9505": (
                "Python filename %r must not start with an underscore",
                "private-module-name",
                "Only __init__.py may start with an underscore.",
            ),
            "C9506": (
                "Directory %s must contain __init__.py",
                "missing-package-init",
                "Every directory containing Python files, except the repository root, must be a package.",
            ),
        }
        self.reported_packages: set[Path] = set()

    def open(self) -> None:
        self.reported_packages.clear()

    def check_name(self, node: nodes.NodeNG, name: str, kind: str) -> None:
        if not name.startswith("_") or (
            name == "_" and kind in {"Variable", "Import"}
        ):
            return
        if (
            kind != "Class"
            and len(name) > 4
            and name.startswith("__")
            and name.endswith("__")
        ):
            return
        self.add_message("private-name", node=node, args=(kind, name))

    def visit_module(self, node: nodes.Module) -> None:
        if node.file is None:
            return
        path = Path(node.file).resolve()
        if path.name.startswith("_") and path.name != "__init__.py":
            self.add_message(
                "private-module-name", node=node, line=1, args=(path.name,)
            )
        self.check_package(node, path.parent)

    def check_package(self, node: nodes.Module, directory: Path) -> None:
        if directory == PROJECT_ROOT or directory in self.reported_packages:
            return
        if not (directory / "__init__.py").is_file():
            self.reported_packages.add(directory)
            self.add_message(
                "missing-package-init",
                node=node,
                line=1,
                args=(str(directory),),
            )

    def visit_classdef(self, node: nodes.ClassDef) -> None:
        self.check_name(node, node.name, "Class")

    def visit_functiondef(self, node: nodes.FunctionDef) -> None:
        self.check_name(node, node.name, "Function")

    visit_asyncfunctiondef = visit_functiondef

    def visit_assignname(self, node: nodes.AssignName) -> None:
        self.check_name(node, node.name, "Variable")

    def visit_assignattr(self, node: nodes.AssignAttr) -> None:
        self.check_name(node, node.attrname, "Attribute")

    def visit_import(self, node: nodes.Import) -> None:
        for name, alias in node.names:
            self.check_name(node, alias or name.split(".")[0], "Import")

    def visit_importfrom(self, node: nodes.ImportFrom) -> None:
        for name, alias in node.names:
            self.check_name(node, alias or name, "Import")


def register(linter: PyLinter) -> None:
    linter.register_checker(NamesChecker(linter))

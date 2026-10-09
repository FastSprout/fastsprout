"""Require explicit exports in every FastSprout library module."""

from pathlib import Path

import astroid.nodes as nodes
from astroid.exceptions import AstroidImportError
from astroid.util import safe_infer
from pylint.checkers import BaseChecker
from pylint.lint import PyLinter

__all__ = ["ModuleExportsChecker", "register"]

LIBRARY_ROOT = Path(__file__).resolve().parents[2] / "src" / "fastsprout"


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
            "C9503": (
                "%s is not exported by %s.__all__",
                "import-outside-all",
                "Import only names declared in the source module's __all__.",
            ),
        }

    def visit_module(self, node: nodes.Module) -> None:
        if node.file is None or not Path(node.file).resolve().is_relative_to(
            LIBRARY_ROOT
        ):
            return
        if not any(
            isinstance(binding.parent, nodes.Assign | nodes.AnnAssign)
            and binding.parent.value is not None
            and binding.scope() is node
            for binding in node.locals.get("__all__", ())
        ):
            self.add_message("missing-module-all", node=node, line=1)

    def visit_importfrom(self, node: nodes.ImportFrom) -> None:
        try:
            module = node.do_import_module()
        except AstroidImportError:
            return
        if "__all__" not in module.locals:
            return
        exports = self.exported_names(module)
        for name, _ in node.names:
            if name != "*" and name not in exports:
                self.add_message(
                    "import-outside-all", node=node, args=(name, module.name)
                )

    def exported_names(self, module: nodes.Module) -> set[str]:
        exports = set(module.wildcard_import_names())
        for call in module.nodes_of_class(nodes.Call):
            exports.update(self.added_exports(call))
        for assignment in module.nodes_of_class(nodes.AugAssign):
            if (
                assignment.scope() is module
                and isinstance(assignment.target, nodes.AssignName)
                and assignment.target.name == "__all__"
                and assignment.op == "+="
            ):
                exports.update(self.sequence_names(assignment.value))
        return exports

    def added_exports(self, call: nodes.Call) -> set[str]:
        function = call.func
        if not (
            call.scope() is call.root()
            and isinstance(function, nodes.Attribute)
            and isinstance(function.expr, nodes.Name)
            and function.expr.name == "__all__"
            and len(call.args) == 1
        ):
            return set()
        if function.attrname == "extend":
            return self.sequence_names(call.args[0])
        value = safe_infer(call.args[0])
        if (
            function.attrname == "append"
            and isinstance(value, nodes.Const)
            and isinstance(value.value, str)
        ):
            return {value.value}
        return set()

    def sequence_names(self, node: nodes.NodeNG) -> set[str]:
        value = safe_infer(node)
        if not isinstance(value, nodes.List | nodes.Tuple):
            return set()
        return {
            element.value
            for item in value.elts
            if isinstance(element := safe_infer(item), nodes.Const)
            and isinstance(element.value, str)
        }


def register(linter: PyLinter) -> None:
    linter.register_checker(ModuleExportsChecker(linter))

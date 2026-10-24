"""Check FastSprout's typed BDD declarations."""

import re
import tokenize
from itertools import chain

import astroid.nodes as nodes
from astroid.util import safe_infer
from pylint.checkers import BaseChecker
from pylint.lint import PyLinter

__all__ = ["TestingPhasesChecker", "register"]

PHASES = {
    f"fastsprout.testing.core.steps.{phase}"
    for phase in ("given", "when", "then")
}


class TestingPhasesChecker(BaseChecker):
    name = "fastsprout-testing"

    def __init__(self, linter: PyLinter) -> None:
        super().__init__(linter)
        self.msgs = {
            "C9507": (
                "Use one BDD phase decorator per function",
                "conflicting-test-phases",
                "Declare given, when, and then in separate functions.",
            ),
            "C9508": (
                "BDD phase requires a type annotation for %s",
                "untyped-test-phase",
                "Annotate phase parameters and return values; self and cls are implicit.",
            ),
            "C9509": (
                "BDD decorators already identify the phase; remove the section comment",
                "redundant-test-phase-comment",
                "Do not repeat BDD phases with given/when/then comments.",
            ),
            "C9510": (
                "Use separate when and then phases",
                "combined-test-phase-comment",
                "Keep test execution and verification in distinct phases.",
            ),
        }
        self.phase_comments: set[int] = set()

    def visit_module(self, node: nodes.Module) -> None:
        source = node.stream()
        self.phase_comments.clear()
        if source is None:
            return
        with source:
            comments = [
                token
                for token in tokenize.tokenize(source.readline)
                if token.type == tokenize.COMMENT
            ]
            for token in comments:
                if re.fullmatch(r"#\s*when\s*/\s*then\s*", token.string):
                    self.add_message(
                        "combined-test-phase-comment",
                        node=node,
                        line=token.start[0],
                    )
            self.phase_comments = {
                token.start[0]
                for token in comments
                if re.fullmatch(r"#\s*(given|when|then)\s*", token.string)
            }

    def is_phase(self, decorator: nodes.NodeNG) -> bool:
        target = (
            decorator.func if isinstance(decorator, nodes.Call) else decorator
        )
        function = safe_infer(target)
        return (
            isinstance(function, nodes.FunctionDef)
            and function.qname() in PHASES
        )

    def visit_functiondef(self, node: nodes.FunctionDef) -> None:
        if node.decorators is None:
            return
        phases = sum(
            self.is_phase(decorator) for decorator in node.decorators.nodes
        )
        if not phases:
            return
        if phases > 1:
            self.add_message("conflicting-test-phases", node=node)
        self.check_annotations(node)
        self.check_comments(node)

    visit_asyncfunctiondef = visit_functiondef

    def check_comments(self, node: nodes.FunctionDef) -> None:
        for line in sorted(self.phase_comments):
            if node.fromlineno <= line <= node.tolineno:
                self.add_message(
                    "redundant-test-phase-comment", node=node, line=line
                )

    def check_annotations(self, node: nodes.FunctionDef) -> None:
        args = node.args
        pairs = chain(
            zip(args.posonlyargs, args.posonlyargs_annotations, strict=True),
            zip(args.args or (), args.annotations, strict=True),
            zip(args.kwonlyargs, args.kwonlyargs_annotations, strict=True),
        )
        annotations: list[tuple[str | None, nodes.NodeNG | None]] = [
            (argument.name, annotation) for argument, annotation in pairs
        ]
        annotations.extend(
            (
                ("return", node.returns),
                (args.vararg, args.varargannotation),
                (args.kwarg, args.kwargannotation),
            )
        )
        for name, annotation in annotations:
            if name and name not in {"self", "cls"} and annotation is None:
                self.add_message("untyped-test-phase", node=node, args=(name,))


def register(linter: PyLinter) -> None:
    linter.register_checker(TestingPhasesChecker(linter))

"""Turn matched step texts into pytest parameter sets."""

import re
from collections.abc import Callable, Iterable, Sequence
from inspect import Signature
from string import Formatter

import pytest

from fastsprout.core import dataclass
from fastsprout.core.types.protocols.ables import Hashable

from .contracts import FIXTURE_CONTRACTS, checked_signature

__all__ = ["STEP_PARAMETERS", "StepPattern", "parameter_key", "parameterize"]

type StepValue = str | int | float

STEP_PARAMETERS: pytest.StashKey[dict[tuple[str, str], frozenset[str]]] = (
    pytest.StashKey()
)


def parameter_key(item: pytest.Function) -> tuple[str, str]:
    return (
        item.parent.nodeid if item.parent else "",
        item.originalname or item.name,
    )


CONVERTERS: dict[str, tuple[str, Callable[[str], StepValue]]] = {
    "": (".*?", str),
    "d": (r"[+-]?\d+", int),
    "f": (r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?", float),
}


@dataclass(frozen=True)
class StepPattern:
    expression: re.Pattern[str]
    converters: dict[str, Callable[[str], StepValue]]

    @classmethod
    def compile(cls, description: str, signature: Signature) -> "StepPattern":
        parts: list[str] = []
        converters: dict[str, Callable[[str], StepValue]] = {}
        for literal, name, specification, conversion in Formatter().parse(
            description
        ):
            parts.append(re.escape(literal))
            if name is None:
                continue
            if name not in signature.parameters or name in converters:
                raise ValueError(
                    f"Step field {name!r} must name a distinct function parameter"
                )
            if conversion or specification not in CONVERTERS:
                raise ValueError(
                    f"Unsupported step format for {name!r}: {specification!r}"
                )
            expression, converters[name] = CONVERTERS[specification]
            parts.append(f"(?P<{name}>{expression})")
        return cls(re.compile("".join(parts)), converters)

    def match(self, text: str) -> dict[str, StepValue] | None:
        matched = self.expression.fullmatch(text)
        return (
            None
            if matched is None
            else {
                name: convert(matched.group(name))
                for name, convert in self.converters.items()
            }
        )


def patterns_for(
    metafunc: pytest.Metafunc, functions: Iterable[Hashable]
) -> list[StepPattern]:
    patterns = [
        StepPattern.compile(contract.description, contract.signature)
        for function in functions
        if (contract := FIXTURE_CONTRACTS.get(function)) is not None
    ]
    assertion = metafunc.definition.get_closest_marker("fastsprout_typed")
    if assertion is not None:
        patterns.append(
            StepPattern.compile(
                assertion.kwargs["description"],
                checked_signature(metafunc.function),
            )
        )
    return patterns


def matched_case(
    texts: Sequence[str], patterns: Sequence[StepPattern]
) -> dict[str, StepValue]:
    values: dict[str, StepValue] = {}
    for text in texts:
        matches = [
            fields
            for pattern in patterns
            if (fields := pattern.match(text)) is not None
        ]
        if len(matches) != 1:
            raise ValueError(
                f"Step {text!r} must match exactly one declared phase"
            )
        for name, value in matches[0].items():
            if name in values and values[name] != value:
                raise ValueError(f"Conflicting step values for {name!r}")
            values[name] = value
    return values


def parameterize(
    metafunc: pytest.Metafunc,
    marker: pytest.Mark,
    functions: Iterable[Hashable],
) -> None:
    try:
        patterns = patterns_for(metafunc, functions)
        rows = [matched_case(texts, patterns) for texts in marker.args]
        if not rows:
            raise ValueError("steps requires at least one case")
        names = tuple(rows[0])
        if any(row.keys() != rows[0].keys() for row in rows):
            raise ValueError("Step cases must provide the same named fields")
        metafunc.parametrize(
            names,
            [tuple(row[name] for name in names) for row in rows],
            ids=marker.kwargs.get("ids"),
        )
        metafunc.config.stash.setdefault(STEP_PARAMETERS, {})[
            parameter_key(metafunc.definition)
        ] = frozenset(names)
    except ValueError as error:
        raise pytest.UsageError(str(error)) from error

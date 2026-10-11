# Shared source rules

## Instruction scope

Before modifying files, read the applicable nested `AGENTS.md` files along
their directory paths. Parent rules remain active; nested rules add local
requirements and take precedence within their scope when rules conflict.
Paths in these instructions are relative to the repository root.

- `src/fastsprout/AGENTS.md`: library rules, with module rules in `core/`,
  `actions/`, `data/`, and `events/`.
- `src/tests/AGENTS.md`: test structure and reuse.

## Small, purposeful changes

Keep changes small, clear, and well designed. Every changed line must have a
concrete purpose that supports the requested behavior. A change without a
clear purpose is a bad change and must be removed. Prefer the smallest
coherent fix; do not add unrelated refactors, abstractions, or speculative
features.

Approaching 500 changed lines of production code (additions and deletions,
including untracked files) is a large change. Before expanding it, reassess
whether each part is necessary and can reuse existing code. Simplify or split
the work into coherent stages where possible; 500 lines is a review trigger,
not a target or permission to add more code.

## No code generation

Code generation is prohibited. Do not add Python code generators, `.pyi`
stubs, or generated type declarations. Do not solve typing problems by
generating additional code files.

## Linters and type checkers must pass

A change is not complete until the required linters and type checkers pass
with the repository's configuration. Do not disable rules, weaken the
configuration, or exclude files to obtain a passing result.
Do not use `# noqa`, `# type: ignore`, `# pyright: ignore`, or casts to hide
errors instead of fixing their cause.
If a required check fails or cannot be run, report this explicitly and do
not present the work as complete.

Every suppression (`noqa`, `type: ignore`, `pyright: ignore`, or Pylint
disable) and every test skip must include a one-sentence explanation of
the concrete reason. An explanation does not authorize a new suppression.

## Precise typing

`Any`, `object`, `Unknown`, and other broad types used in place of the actual
contract are prohibited, including in implementation code and helper APIs.
This also applies to collections and callables without type parameters,
and to aliases or casts that conceal lost type information.
Use concrete types, precise protocols, and bounded or constrained generics
that preserve field, argument, and result types for IDEs and type checkers.

## No local imports

Imports inside functions, methods, or class bodies are prohibited. Keep
imports at module scope. Typing-only imports may use a module-level
`if TYPE_CHECKING:` block.

## Use the FastSprout dataclass

Use `dataclass` or `typed_dataclass` from `fastsprout.core` instead of the
standard-library decorator, including in examples and tests.
Only `src/fastsprout/core/decorators/dataclasses/dataclass.py` may import
the standard-library decorator to implement the wrapper. Dataclass utilities
such as `fields`, `asdict`, and `is_dataclass` remain allowed.

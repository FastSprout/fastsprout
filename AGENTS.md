# Repository rules

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

## Precise typing

`Any`, `object`, `Unknown`, and other broad types used in place of the actual
contract are prohibited, including in implementation code and helper APIs.
This also applies to collections and callables without type parameters,
and to aliases or casts that conceal lost type information.
Use concrete types, precise protocols, and bounded or constrained generics
that preserve field, argument, and result types for IDEs and type checkers.

## Explicit module exports

Every Python module under `src/fastsprout` must define `__all__`, including
package `__init__.py` files. Use an empty list when a module has no exports.

## No local imports

Imports inside functions, methods, or class bodies are prohibited. Keep
imports at module scope. Typing-only imports may use a module-level
`if TYPE_CHECKING:` block.

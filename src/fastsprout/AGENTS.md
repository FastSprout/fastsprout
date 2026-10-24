# Library rules

## Explicit module exports

Every Python module under `src/fastsprout` must define `__all__`, including
package `__init__.py` files. Use an empty list when a module has no exports.
Import public symbols declared in the owning module's `__all__`.

## Protocol names

Name protocols with the suffix `able` so their names distinguish contracts
from implementations. Apply this convention to public and internal protocols;
keep their declarations, exports, imports, and uses consistent.
Reserve the `Base` prefix for base classes; protocol names must not use it.

## Layer boundaries and reuse

Follow the dependency direction and module boundaries in `.importlinter`.
Reuse existing contracts and implementations before adding helpers or
abstractions. Keep backend and transport details in their owning layers;
shared contracts must remain usable with other implementations.
Preserve the optional dependency boundaries declared in `pyproject.toml`.

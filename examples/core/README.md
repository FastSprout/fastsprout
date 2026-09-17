# Examples

Runnable snippets. Each file is self-contained. Run from the repository root
with the SQL extra used by these examples:

```bash
uv run --extra data-sql python examples/core/01_base_schema.py
```

| File | Shows |
|---|---|
| `01_base_schema.py` | `BaseSchema` with snake↔camel aliasing |
| `02_typed_dataclass.py` | `@typed_dataclass` + `Field[T]` |
| `03_typed_pyd_dataclass.py` | Pydantic dataclass with runtime validation |
| `04_field_assignment.py` | `Field.set(...)` for partial updates |
| `05_field_ref_orm.py` | `HasOrm` + `FieldRef.orm` with SQLModel |
| `06_action.py` | `BaseAction` — single result, class + function |
| `07_action_sequence.py` | `BaseSequenceAction` — eager collection, class + function |
| `08_action_iterable.py` | `BaseIterableAction` — lazy sync iterable, class + function |
| `09_action_iterator.py` | `BaseIteratorAction` — async streaming, class + function |
| [10_dto_visibility.py](10_dto_visibility.py) | One entity, read/write/combined DTOs, typed fields and runtime guards |
| [11_dto_sql.py](11_dto_sql.py) | SQL entity inheritance, UUID defaults, DTO subclasses and unchanged ORM mappings |

## DTO examples

```bash
uv run --extra data-sql python examples/core/10_dto_visibility.py
uv run --extra data-sql python examples/core/11_dto_sql.py
```

Each example includes assertions and commented accesses that mypy/basedpyright
reject. Uncomment those lines to inspect the diagnostics in your IDE.

DTO constructors check required, unknown, and forbidden field names at runtime;
they do not validate input values. `ReadWriteDTO` selects the union of visible
fields and retains required fields. See the [DTO contract](../../docs/dto_visibility.md)
for details.

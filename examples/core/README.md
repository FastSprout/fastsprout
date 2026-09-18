# Examples

Runnable snippets. Each file is self-contained. Run from the repository root
with the SQL extra used by these examples:

```bash
uv run --extra data-sql python examples/core/01_base_schema.py
```

| File | Shows |
|---|---|
| [01_base_schema.py](01_base_schema.py) | `BaseSchema` with snake↔camel aliasing |
| [02_typed_dataclass.py](02_typed_dataclass.py) | `@typed_dataclass` + `Field[T]` |
| [03_typed_pyd_dataclass.py](03_typed_pyd_dataclass.py) | Pydantic dataclass with runtime validation |
| [04_field_assignment.py](04_field_assignment.py) | `Field.set(...)` for partial updates |
| [05_field_ref_orm.py](05_field_ref_orm.py) | `HasOrm` + `FieldRef.orm` with SQLModel |
| [06_action.py](06_action.py) | `BaseAction` — single result, class + function |
| [07_action_sequence.py](07_action_sequence.py) | `BaseSequenceAction` — eager collection, class + function |
| [08_action_iterable.py](08_action_iterable.py) | `BaseIterableAction` — lazy sync iterable, class + function |
| [09_action_iterator.py](09_action_iterator.py) | `BaseIteratorAction` — async streaming, class + function |
| [10_dto_visibility.py](10_dto_visibility.py) | One entity, read/write/combined DTOs, typed fields and runtime guards |
| [11_dto_sql.py](11_dto_sql.py) | SQL entity inheritance, UUID defaults, DTO subclasses and unchanged ORM mappings |

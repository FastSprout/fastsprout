# Examples

Runnable snippets. Each file is self-contained:

```bash
uv run python examples/01_base_schema.py
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

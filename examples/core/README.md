# CORE Examples

Runnable snippets. Each file is self-contained. Run from the repository root with the SQL extra used by these examples:

```bash
uv run --extra data-sql python examples/core/01_base_schema.py
```

---

| File | Shows |
| --- | --- |
| [01_base_schema.py](01_base_schema.py) | BaseSchema — Pydantic model with snake_case <-> camelCase aliasing. |
| [02_typed_dataclass.py](02_typed_dataclass.py) | @typed_dataclass — stdlib @dataclass + Field[T] descriptors. |
| [03_typed_pyd_dataclass.py](03_typed_pyd_dataclass.py) | @typed_pydantic_dataclass — Pydantic dataclass + Field[T] descriptors. |
| [04_field_assignment.py](04_field_assignment.py) | Field.set(value) -> FieldAssignment[T]. |
| [05_field_ref_orm.py](05_field_ref_orm.py) | HasOrm + FieldRef.orm with SQLModel. |
| [06_action.py](06_action.py) | BaseAction — single typed result. Class and function styles. |
| [07_action_sequence.py](07_action_sequence.py) | BaseSequenceAction — eager collection (list/tuple). Class and function styles. |
| [08_action_iterable.py](08_action_iterable.py) | BaseIterableAction — lazy sync iterable (generator). Class and function styles. |
| [09_action_iterator.py](09_action_iterator.py) | BaseIteratorAction — async streaming (async-gen). Class and function styles. |
| [10_dto_visibility.py](10_dto_visibility.py) | Declare fields once, then derive DTOs by choosing a visibility base. |
| [11_dto_sql.py](11_dto_sql.py) | Derive a DTO from a SQL entity and extend it with ordinary inheritance. |

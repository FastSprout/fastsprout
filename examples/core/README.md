# CORE Examples

The core layer defines typed schemas, fields, actions, and DTO
visibility shared by the other layers. Run from the repository root:

```bash
uv run python examples/core/01_typed_object_01_typed_dataclass.py
```

The SQL entity examples need `--extra data-sql`.

## 1. Typed Object

| File | Shows |
| --- | --- |
| [01_typed_object_01_typed_dataclass.py](01_typed_object_01_typed_dataclass.py) | @typed_dataclass — stdlib @dataclass + Field[T] descriptors. |
| [01_typed_object_02_typed_pyd_dataclass.py](01_typed_object_02_typed_pyd_dataclass.py) | @typed_pydantic_dataclass — Pydantic dataclass + Field[T] descriptors. |
| [01_typed_object_03_base_schema.py](01_typed_object_03_base_schema.py) | BaseSchema — Pydantic model with snake_case <-> camelCase aliasing. |

## 2. Fields

| File | Shows |
| --- | --- |
| [02_fields_01_field_ref_orm.py](02_fields_01_field_ref_orm.py) | HasOrm + FieldRef.orm with SQLModel. |
| [02_fields_02_field_assignment.py](02_fields_02_field_assignment.py) | Field.set(value) -> FieldAssignment[T]. |

## 3. Action

| File | Shows |
| --- | --- |
| [03_action_01_base_action.py](03_action_01_base_action.py) | BaseAction — single typed result. Class and function styles. |
| [03_action_02_action_sequence.py](03_action_02_action_sequence.py) | BaseSequenceAction — eager collection (list/tuple). Class and function styles. |
| [03_action_03_action_iterable.py](03_action_03_action_iterable.py) | Return greetings lazily from a class action or an async function. |
| [03_action_03_action_iterator.py](03_action_03_action_iterator.py) | BaseIteratorAction — async streaming (async-gen). Class and function styles. |

## 4. DTO

| File | Shows |
| --- | --- |
| [04_dto_01_visibility.py](04_dto_01_visibility.py) | Declare fields once, then derive DTOs by choosing a visibility base. |
| [04_dto_02_sql.py](04_dto_02_sql.py) | Derive a DTO from a SQL entity and extend it with ordinary inheritance. |
| [04_dto/03_extra_fields.py](04_dto/03_extra_fields.py) | Expose extra read and write fields only when explicitly requested. |

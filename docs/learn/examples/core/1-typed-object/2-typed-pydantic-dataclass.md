# 2. Typed Pydantic Dataclass

<!-- example-source: examples/core/01_typed_object/02_typed_pyd_dataclass.py -->

@typed_pydantic_dataclass — Pydantic dataclass + Field[T] descriptors.

Lighter than BaseSchema (no BaseModel machinery) but keeps runtime
validation through Pydantic.

## Source

```{.python}
--8<-- "examples/core/01_typed_object/02_typed_pyd_dataclass.py"
```

## Result

```text
User(field_int=1, field_str='alice')
Validation rejected bad payload: ('field_int',)
```

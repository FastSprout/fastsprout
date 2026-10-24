# 1. Typed Dataclass

<!-- example-source: examples/core/01_typed_object/01_typed_dataclass.py -->

@typed_dataclass — stdlib @dataclass + Field[T] descriptors.

Same Field[T] declaration ergonomics as BaseSchema, no Pydantic overhead,
no runtime validation. Useful for internal value objects.

## Source

```{.python}
--8<-- "examples/core/01_typed_object/01_typed_dataclass.py"
```

## Result

```text
Point(x=1, y=2, label='origin-ish')
<Point.x>
```

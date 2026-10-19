# 3. Properties

<!-- example-source: examples/testing/01_core/03_properties.py -->

Run typed Hypothesis properties through pytest.

## Source

```python
"""Run typed Hypothesis properties through pytest."""

from fastsprout.testing.core.properties import given, strategies


@given(strategies.integers(), strategies.integers())
def test_addition_is_commutative(x: int, y: int) -> None:
    assert x + y == y + x
```

## Result

```text

examples/testing/01_core/03_properties.py::test_addition_is_commutative PASSED [100%]
```

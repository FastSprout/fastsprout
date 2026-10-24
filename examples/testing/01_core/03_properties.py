"""Run typed Hypothesis properties through pytest."""

from fastsprout.testing.core.properties import given, strategies


@given(strategies.integers(), strategies.integers())
def test_addition_is_commutative(x: int, y: int) -> None:
    assert x + y == y + x

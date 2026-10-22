import pytest

from fastsprout.data.capabilities.query import Eq, Expression, In
from fastsprout.data.capabilities.query.predicate import evaluate
from fastsprout.testing.core import given, then, when


def positive(value: int) -> bool:
    return value > 0


class TestEntityPredicates:
    @given("a comparison around a predicate instead of a field value")
    def condition(self, membership: bool) -> Expression[int]:
        return In([positive]) if membership else Eq(positive)

    @when("the comparison is evaluated as an entity condition")
    async def rejected(self, condition: Expression[int]) -> TypeError | None:
        try:
            await evaluate(condition, 1)
        except TypeError as error:
            return error
        return None

    @pytest.mark.parametrize("membership", [False, True])
    @then("entity conditions require predicates or explicit field comparisons")
    def test_comparison_without_field(self, rejected: TypeError | None) -> None:
        assert isinstance(rejected, TypeError)
        assert str(rejected) == (
            "Entity filters require field conditions or predicates"
        )

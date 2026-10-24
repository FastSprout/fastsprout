import pytest

from fastsprout.actions.workflows.execution import execute

from ..types.common import Amount


async def test_execute_rejects_non_schema_input_at_runtime() -> None:
    async def first(value: Amount) -> Amount:
        return value

    with pytest.raises(TypeError, match="Workflow input must be a Schema"):
        async for _ in execute(first, 123):
            pytest.fail("Invalid input produced a result")
